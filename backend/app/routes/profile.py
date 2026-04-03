from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import AvailabilityLevel, ExperienceLevel, Skill, User


profile_bp = Blueprint("profile_bp", __name__)


def _require_json() -> dict:
    if not request.is_json:
        return {}
    return request.get_json(silent=True) or {}


def _parse_experience_level(value: str) -> str:
    v = (value or "").strip()
    choices = {e.value for e in ExperienceLevel}
    if v not in choices:
        raise ValueError(f"Invalid experience level: {v}")
    return v


def _parse_availability_level(value: str) -> str:
    v = (value or "").strip()
    choices = {a.value for a in AvailabilityLevel}
    if v not in choices:
        raise ValueError(f"Invalid availability: {v}")
    return v


@profile_bp.get("/profile/me")
@jwt_required()
def profile_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"}), 404

    return jsonify(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "skills": user.skills or [],
            "experience_level": user.experience_level,
            "availability": user.availability,
            "github_url": user.github_url,
            "profile_rating_avg": user.rating_average(),
        }
    )


@profile_bp.put("/profile")
@jwt_required()
def profile_update():
    data = _require_json()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"}), 404

    name = (data.get("name") or "").strip()
    if name:
        user.name = name
    bio = data.get("bio")
    if bio is not None:
        user.bio = str(bio).strip()

    if "skills" in data:
        user.skills = User.normalize_skill_list(data.get("skills") or [])
        User.ensure_global_skills(user.skills)

    if "experience_level" in data:
        try:
            user.experience_level = _parse_experience_level(data.get("experience_level"))
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    if "availability" in data:
        try:
            user.availability = _parse_availability_level(data.get("availability"))
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    github_url = data.get("github_url")
    if github_url is not None:
        url = str(github_url).strip()
        user.github_url = url or None

    db.session.commit()
    return jsonify({"message": "profile updated"}), 200


@profile_bp.get("/skills")
@jwt_required(optional=True)
def list_skills():
    skills = [s.name for s in Skill.query.order_by(Skill.name.asc()).all()]
    return jsonify({"skills": skills})

