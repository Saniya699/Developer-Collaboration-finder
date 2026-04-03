from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Project, Skill, User
from ..utils.matching import (
    _cosine_sim,
    _exp_compat,
    _availability_compat,
    _get_skill_index_map,
    _vectorize_binary,
    score_match,
    skill_gap,
)


matching_bp = Blueprint("matching_bp", __name__)


def _skill_index_map():
    names = [s.name for s in Skill.query.order_by(Skill.name.asc()).all()]
    return _get_skill_index_map(names)


def _set(skills):
    return {s.strip().lower() for s in (skills or []) if isinstance(s, str) and s.strip()}


def _serialize_user(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "skills": u.skills or [],
        "experience_level": u.experience_level,
        "availability": u.availability,
        "profile_rating_avg": u.rating_average(),
    }


@matching_bp.get("/matches/teammates")
@jwt_required()
def recommend_teammates():
    me = User.query.get(int(get_jwt_identity()))
    if not me:
        return jsonify({"message": "user not found"}), 404

    top = int(request.args.get("top") or 10)
    project_id = request.args.get("project_id", type=int)

    skill_index_map = _skill_index_map()

    me_skills_set = _set(me.skills)
    me_vec = _vectorize_binary(me.skills or [], skill_index_map)

    candidates = []

    if project_id:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"message": "project not found"}), 404

        project_required_set = _set(project.required_skills)
        project_vec = _vectorize_binary(project.required_skills or [], skill_index_map)

        member_ids = {m.user_id for m in project.members}
        # Avoid recommending the current user or existing members.
        user_q = User.query.filter(User.id != me.id)
        for u in user_q.all():
            if u.id in member_ids:
                continue
            u_skills_set = _set(u.skills)
            # Prefilter for skill overlap to reduce work on large datasets.
            if project_required_set and not (u_skills_set & project_required_set):
                continue

            skill_sim = _cosine_sim(project_vec, _vectorize_binary(u.skills or [], skill_index_map))
            exp_compat = _exp_compat(me.experience_level, u.experience_level)
            avail_compat = _availability_compat(me.availability, u.availability)
            # Score uses user->project skill similarity indirectly via project_required_vec.
            s = score_match(skill_sim, exp_compat, avail_compat)

            gap = skill_gap(u.skills or [], project.required_skills or [])
            candidates.append(
                {
                    "user": _serialize_user(u),
                    "overall_score": s.overall,
                    "skill_similarity": s.skill_similarity,
                    "experience_compatibility": s.experience_compatibility,
                    "availability_compatibility": s.availability_compatibility,
                    "missing_skills_for_project": gap["missing_skills"],
                }
            )
    else:
        # User <-> User matching (team suggestions)
        user_q = User.query.filter(User.id != me.id)
        for u in user_q.all():
            u_skills_set = _set(u.skills)
            if me_skills_set and not (u_skills_set & me_skills_set):
                continue

            u_vec = _vectorize_binary(u.skills or [], skill_index_map)
            skill_sim = _cosine_sim(me_vec, u_vec)
            exp_compat = _exp_compat(me.experience_level, u.experience_level)
            avail_compat = _availability_compat(me.availability, u.availability)
            s = score_match(skill_sim, exp_compat, avail_compat)
            candidates.append(
                {
                    "user": _serialize_user(u),
                    "overall_score": s.overall,
                    "skill_similarity": s.skill_similarity,
                    "experience_compatibility": s.experience_compatibility,
                    "availability_compatibility": s.availability_compatibility,
                }
            )

    candidates.sort(key=lambda x: x["overall_score"], reverse=True)
    return jsonify({"items": candidates[:top] if top > 0 else candidates})


@matching_bp.get("/matches/projects")
@jwt_required()
def recommend_projects():
    me = User.query.get(int(get_jwt_identity()))
    if not me:
        return jsonify({"message": "user not found"}), 404

    top = int(request.args.get("top") or 10)
    status = (request.args.get("status") or "Open").strip()

    skill_index_map = _skill_index_map()
    me_vec = _vectorize_binary(me.skills or [], skill_index_map)
    me_skills_set = _set(me.skills)

    q = Project.query
    if status:
        q = q.filter(Project.status == status)
    q = q.order_by(Project.created_at.desc())

    # Exclude projects where I'm already a member.
    member_project_ids = {m.project_id for m in project_members_for_user(me.id)}
    candidates = []
    for p in q.all():
        if p.id in member_project_ids:
            continue
        req_set = _set(p.required_skills)
        if me_skills_set and req_set and not (me_skills_set & req_set):
            continue

        p_vec = _vectorize_binary(p.required_skills or [], skill_index_map)
        skill_sim = _cosine_sim(me_vec, p_vec)

        creator_exp = p.creator.experience_level if p.creator else me.experience_level
        creator_av = p.creator.availability if p.creator else me.availability

        exp_compat = _exp_compat(me.experience_level, creator_exp)
        avail_compat = _availability_compat(me.availability, creator_av)

        s = score_match(skill_sim, exp_compat, avail_compat)
        gap = skill_gap(me.skills or [], p.required_skills or [])

        candidates.append(
            {
                "project": {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "required_skills": p.required_skills or [],
                    "max_team_size": p.max_team_size,
                    "status": p.status,
                    "members_count": len(p.members),
                },
                "overall_score": s.overall,
                "skill_similarity": s.skill_similarity,
                "experience_compatibility": s.experience_compatibility,
                "availability_compatibility": s.availability_compatibility,
                "missing_skills": gap["missing_skills"],
            }
        )

    candidates.sort(key=lambda x: x["overall_score"], reverse=True)
    return jsonify({"items": candidates[:top] if top > 0 else candidates})


def project_members_for_user(user_id: int):
    # Small helper so we can compute project membership IDs efficiently.
    from ..models import ProjectMember

    return ProjectMember.query.filter_by(user_id=user_id).all()


@matching_bp.get("/matches/projects/<int:project_id>/gap")
@jwt_required()
def gap_analyzer(project_id: int):
    me = User.query.get(int(get_jwt_identity()))
    if not me:
        return jsonify({"message": "user not found"}), 404
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404

    gap = skill_gap(me.skills or [], project.required_skills or [])
    return jsonify(
        {
            "project_id": project.id,
            "required_skills": project.required_skills or [],
            "user_skills": me.skills or [],
            "missing_skills": gap["missing_skills"],
            "matched_skills": gap["matched_skills"],
        }
    )

