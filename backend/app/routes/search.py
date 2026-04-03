from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Project, ProjectStatus, User, Skill
from ..utils.matching import _availability_compat, _exp_compat, _cosine_sim, _get_skill_index_map, _vectorize_binary, score_match, skill_gap
from ..extensions import db


search_bp = Blueprint("search_bp", __name__)


def _parse_csv(value: str | None):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in value.split(",") if isinstance(v, str) and v.strip()]


@search_bp.get("/search/projects")
@jwt_required(optional=True)
def search_projects():
    # If authenticated, we rank by local user->project matching.
    user_id = None
    try:
        user_id = int(get_jwt_identity()) if get_jwt_identity() is not None else None
    except Exception:
        user_id = None

    status = (request.args.get("status") or "").strip()
    skills_param = _parse_csv(request.args.get("skills"))
    experience_level = (request.args.get("experience_level") or "").strip()
    availability = (request.args.get("availability") or "").strip()
    top = int(request.args.get("top") or 20)

    skill_index_map = _get_skill_index_map([s.name for s in Skill.query.order_by(Skill.name.asc()).all()])

    if user_id:
        me = User.query.get(user_id)
        if not me:
            return jsonify({"message": "user not found"}), 404
        skills = me.skills or []
        experience_level = me.experience_level
        availability = me.availability
    else:
        skills = skills_param

    me_vec = _vectorize_binary(skills or [], skill_index_map)
    me_skill_set = {s.strip().lower() for s in (skills or []) if isinstance(s, str) and s.strip()}

    q = Project.query
    if status:
        if status not in {s.value for s in ProjectStatus}:
            return jsonify({"message": "invalid status"}), 400
        q = q.filter(Project.status == status)
    q = q.order_by(Project.created_at.desc())

    candidates = []
    for p in q.all():
        req_set = {s.strip().lower() for s in (p.required_skills or []) if isinstance(s, str) and s.strip()}
        if me_skill_set and req_set and not (me_skill_set & req_set):
            continue

        # Basic compatibility via the project creator (proxy).
        creator_exp = p.creator.experience_level if p.creator else experience_level
        creator_av = p.creator.availability if p.creator else availability
        if experience_level and creator_exp and creator_exp != experience_level:
            # still allow but score will reduce; only hard-filter if provided explicitly
            pass
        if availability and creator_av and creator_av != availability:
            pass

        p_vec = _vectorize_binary(p.required_skills or [], skill_index_map)
        skill_sim = _cosine_sim(me_vec, p_vec)
        exp_compat = _exp_compat(experience_level, creator_exp)
        avail_compat = _availability_compat(availability, creator_av)
        s = score_match(skill_sim, exp_compat, avail_compat)

        gap = skill_gap(skills or [], p.required_skills or [])
        candidates.append(
            {
                "project": {
                    "id": p.id,
                    "title": p.title,
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
    return jsonify({"items": candidates[:top] if top > 0 else candidates}), 200


@search_bp.get("/search/teammates")
@jwt_required(optional=True)
def search_teammates():
    user_id = None
    try:
        user_id = int(get_jwt_identity()) if get_jwt_identity() is not None else None
    except Exception:
        user_id = None

    top = int(request.args.get("top") or 20)
    skills_param = _parse_csv(request.args.get("skills"))
    experience_level = (request.args.get("experience_level") or "").strip()
    availability = (request.args.get("availability") or "").strip()

    skill_index_map = _get_skill_index_map([s.name for s in Skill.query.order_by(Skill.name.asc()).all()])

    if user_id:
        me = User.query.get(user_id)
        if not me:
            return jsonify({"message": "user not found"}), 404
        skills = me.skills or []
        experience_level = me.experience_level
        availability = me.availability
        me_id = me.id
    else:
        skills = skills_param
        me_id = None

    me_vec = _vectorize_binary(skills or [], skill_index_map)
    me_skill_set = {s.strip().lower() for s in (skills or []) if isinstance(s, str) and s.strip()}

    q = User.query
    if me_id is not None:
        q = q.filter(User.id != me_id)

    candidates = []
    for u in q.all():
        u_set = {s.strip().lower() for s in (u.skills or []) if isinstance(s, str) and s.strip()}
        if me_skill_set and u_set and not (me_skill_set & u_set):
            continue

        u_vec = _vectorize_binary(u.skills or [], skill_index_map)
        skill_sim = _cosine_sim(me_vec, u_vec)
        exp_compat = _exp_compat(experience_level, u.experience_level)
        avail_compat = _availability_compat(availability, u.availability)
        s = score_match(skill_sim, exp_compat, avail_compat)

        candidates.append(
            {
                "user": {
                    "id": u.id,
                    "name": u.name,
                    "skills": u.skills or [],
                    "experience_level": u.experience_level,
                    "availability": u.availability,
                    "profile_rating_avg": u.rating_average(),
                },
                "overall_score": s.overall,
                "skill_similarity": s.skill_similarity,
                "experience_compatibility": s.experience_compatibility,
                "availability_compatibility": s.availability_compatibility,
            }
        )

    candidates.sort(key=lambda x: x["overall_score"], reverse=True)
    return jsonify({"items": candidates[:top] if top > 0 else candidates}), 200

