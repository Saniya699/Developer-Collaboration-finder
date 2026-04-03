from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import (
    Application,
    ApplicationStatus,
    AvailabilityLevel,
    ExperienceLevel,
    Notification,
    NotificationType,
    Project,
    ProjectMember,
    ProjectStatus,
    User,
)


projects_bp = Blueprint("projects_bp", __name__)


def _require_json() -> dict:
    if not request.is_json:
        return {}
    return request.get_json(silent=True) or {}


@projects_bp.post("/projects")
@jwt_required()
def project_create():
    data = _require_json()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"}), 404

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    required_skills = User.normalize_skill_list(data.get("required_skills") or [])
    max_team_size = int(data.get("max_team_size") or 5)
    status = (data.get("status") or ProjectStatus.OPEN.value).strip()

    if not title:
        return jsonify({"message": "title is required"}), 400
    if max_team_size < 1:
        return jsonify({"message": "max_team_size must be >= 1"}), 400
    if status not in {s.value for s in ProjectStatus}:
        return jsonify({"message": "invalid project status"}), 400
    if not required_skills:
        return jsonify({"message": "required_skills is required"}), 400

    Project.ensure_global_skills = User.ensure_global_skills  # backwards-compatible alias
    User.ensure_global_skills(required_skills)

    project = Project(
        title=title,
        description=description,
        creator_id=user.id,
        required_skills=required_skills,
        max_team_size=max_team_size,
        status=status,
    )
    db.session.add(project)
    db.session.flush()

    # Creator becomes the first member.
    db.session.add(ProjectMember(project_id=project.id, user_id=user.id))
    db.session.commit()

    return jsonify({"message": "project created", "project": _serialize_project(project)}), 201


@projects_bp.get("/projects")
@jwt_required(optional=True)
def project_list():
    user_id = int(get_jwt_identity()) if request.headers.get("Authorization") else None

    page = int(request.args.get("page") or 1)
    per_page = int(request.args.get("per_page") or 10)
    status = (request.args.get("status") or "").strip()

    q = Project.query
    if status:
        if status not in {s.value for s in ProjectStatus}:
            return jsonify({"message": "invalid status filter"}), 400
        q = q.filter(Project.status == status)

    # Newest first.
    q = q.order_by(Project.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    items = [_serialize_project(p, include_members=True) for p in pagination.items]

    return jsonify(
        {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
        }
    )


@projects_bp.put("/projects/<int:project_id>")
@jwt_required()
def project_update(project_id: int):
    data = _require_json()
    user_id = int(get_jwt_identity())
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404
    if project.creator_id != user_id:
        return jsonify({"message": "forbidden"}), 403

    title = data.get("title")
    description = data.get("description")
    required_skills = data.get("required_skills")
    max_team_size = data.get("max_team_size")
    status = data.get("status")

    if title is not None:
        title = str(title).strip()
        if not title:
            return jsonify({"message": "title cannot be empty"}), 400
        project.title = title
    if description is not None:
        project.description = str(description).strip()
    if required_skills is not None:
        req = User.normalize_skill_list(required_skills)
        if not req:
            return jsonify({"message": "required_skills cannot be empty"}), 400
        project.required_skills = req
        User.ensure_global_skills(req)
    if max_team_size is not None:
        mt = int(max_team_size)
        if mt < 1:
            return jsonify({"message": "max_team_size must be >= 1"}), 400
        project.max_team_size = mt
    if status is not None:
        status = str(status).strip()
        if status not in {s.value for s in ProjectStatus}:
            return jsonify({"message": "invalid project status"}), 400
        project.status = status

    db.session.commit()
    return jsonify({"message": "project updated", "project": _serialize_project(project, include_members=True)}), 200


@projects_bp.delete("/projects/<int:project_id>")
@jwt_required()
def project_delete(project_id: int):
    user_id = int(get_jwt_identity())
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404
    if project.creator_id != user_id:
        return jsonify({"message": "forbidden"}), 403

    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "project deleted"}), 200


@projects_bp.post("/projects/<int:project_id>/apply")
@jwt_required()
def project_apply(project_id: int):
    data = _require_json()
    user_id = int(get_jwt_identity())
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404
    if project.status != ProjectStatus.OPEN.value:
        return jsonify({"message": "project is closed"}), 400

    if user_id == project.creator_id:
        return jsonify({"message": "you are the project creator"}), 400

    existing_member = ProjectMember.query.filter_by(project_id=project.id, user_id=user_id).first()
    if existing_member:
        return jsonify({"message": "you are already a member"}), 400

    note = (data.get("message") or "").strip()

    application = Application(
        project_id=project.id,
        applicant_id=user_id,
        status=ApplicationStatus.PENDING.value,
        message=note,
    )
    db.session.add(application)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"message": "application already exists"}), 409

    # Notify project creator about the new application.
    db.session.add(
        Notification(
            user_id=project.creator_id,
            type=NotificationType.APPLICATION_CREATED.value,
            payload={
                "project_id": project.id,
                "application_id": application.id,
                "applicant_id": user_id,
            },
        )
    )
    db.session.commit()

    return jsonify({"message": "application submitted", "application": _serialize_application(application)}), 201


@projects_bp.get("/projects/<int:project_id>/applications")
@jwt_required()
def project_applications(project_id: int):
    user_id = int(get_jwt_identity())
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404
    if project.creator_id != user_id:
        return jsonify({"message": "forbidden"}), 403

    apps = Application.query.filter_by(project_id=project.id).order_by(Application.created_at.desc()).all()
    return jsonify({"items": [_serialize_application(a) for a in apps]}), 200


@projects_bp.post("/projects/<int:project_id>/applications/<int:applicant_id>/decision")
@jwt_required()
def project_decision(project_id: int, applicant_id: int):
    data = _require_json()
    user_id = int(get_jwt_identity())
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"message": "project not found"}), 404
    if project.creator_id != user_id:
        return jsonify({"message": "forbidden"}), 403

    decision = (data.get("decision") or "").strip().lower()
    if decision not in {"accept", "reject"}:
        return jsonify({"message": "decision must be accept or reject"}), 400

    app_obj = Application.query.filter_by(project_id=project.id, applicant_id=applicant_id).first()
    if not app_obj:
        return jsonify({"message": "application not found"}), 404
    if app_obj.status != ApplicationStatus.PENDING.value:
        return jsonify({"message": "application already decided"}), 400

    if decision == "reject":
        app_obj.status = ApplicationStatus.REJECTED.value
        app_obj.decision_at = db.func.now()
        db.session.add(
            Notification(
                user_id=applicant_id,
                type=NotificationType.APPLICATION_REJECTED.value,
                payload={"project_id": project.id, "application_id": app_obj.id, "by_project_creator": user_id},
            )
        )
        db.session.commit()
        return jsonify({"message": "applicant rejected"}), 200

    # Accept:
    current_members = ProjectMember.query.filter_by(project_id=project.id).count()
    if current_members >= project.max_team_size:
        return jsonify({"message": "project is full"}), 400

    app_obj.status = ApplicationStatus.ACCEPTED.value
    app_obj.decision_at = db.func.now()
    db.session.add(ProjectMember(project_id=project.id, user_id=applicant_id))

    # Auto-close when team is full.
    if current_members + 1 >= project.max_team_size:
        project.status = ProjectStatus.CLOSED.value

    db.session.add(
        Notification(
            user_id=applicant_id,
            type=NotificationType.APPLICATION_ACCEPTED.value,
            payload={"project_id": project.id, "application_id": app_obj.id, "by_project_creator": user_id},
        )
    )

    db.session.commit()
    return jsonify({"message": "applicant accepted", "application": _serialize_application(app_obj)}), 200


@projects_bp.get("/projects/me")
@jwt_required()
def projects_my():
    user_id = int(get_jwt_identity())
    membership = ProjectMember.query.filter_by(user_id=user_id).all()
    projects = [m.project for m in membership]
    return jsonify({"items": [_serialize_project(p, include_members=True) for p in projects]}), 200


def _serialize_user_brief(u: User):
    return {"id": u.id, "name": u.name, "skills": u.skills or [], "experience_level": u.experience_level, "availability": u.availability, "profile_rating_avg": u.rating_average()}


def _serialize_application(a: Application):
    applicant = a.applicant
    return {
        "id": a.id,
        "project_id": a.project_id,
        "applicant_id": a.applicant_id,
        "applicant": {
            "id": applicant.id if applicant else a.applicant_id,
            "name": applicant.name if applicant else None,
            "skills": applicant.skills if applicant else [],
            "experience_level": applicant.experience_level if applicant else None,
            "availability": applicant.availability if applicant else None,
            "profile_rating_avg": applicant.rating_average() if applicant else None,
        },
        "status": a.status,
        "message": a.message,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "decision_at": a.decision_at.isoformat() if a.decision_at else None,
    }


def _serialize_project(p: Project, include_members: bool = False):
    members = []
    if include_members:
        members = [
            {
                "id": m.user.id,
                "name": m.user.name,
                "skills": m.user.skills or [],
                "experience_level": m.user.experience_level,
                "availability": m.user.availability,
                "profile_rating_avg": m.user.rating_average(),
            }
            for m in p.members
        ]

    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "creator_id": p.creator_id,
        "required_skills": p.required_skills or [],
        "max_team_size": p.max_team_size,
        "status": p.status,
        "members_count": len(p.members),
        "members": members,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }

