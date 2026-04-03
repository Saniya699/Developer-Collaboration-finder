from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)

from ..extensions import db
from ..models import User


auth_bp = Blueprint("auth_bp", __name__)


def _require_json() -> dict:
    if not request.is_json:
        return {}
    return request.get_json(silent=True) or {}


@auth_bp.post("/register")
def register():
    data = _require_json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"message": "name, email, and password are required"}), 400
    if len(password) < 8:
        return jsonify({"message": "password must be at least 8 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "email already registered"}), 409

    user = User(
        name=name,
        email=email,
        bio=(data.get("bio") or "").strip(),
        skills=User.normalize_skill_list(data.get("skills") or []),
        experience_level=data.get("experience_level") or "Beginner",
        availability=data.get("availability") or "Part-time",
        github_url=(data.get("github_url") or "").strip() or None,
    )
    user.set_password(password)

    # Ensure global skill universe (local-only).
    User.ensure_global_skills(user.skills)

    db.session.add(user)
    db.session.commit()

    # Flask-JWT-Extended expects identity to be JSON-serializable; use string for subject.
    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access, "refresh_token": refresh}), 201


@auth_bp.post("/login")
def login():
    data = _require_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "invalid credentials"}), 401

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify({"access_token": access, "refresh_token": refresh}), 200


@auth_bp.post("/refresh")
def refresh():
    # Using JWT refresh tokens to issue a new access token.
    from flask_jwt_extended import jwt_required

    @jwt_required(refresh=True)
    def _do():
        identity = get_jwt_identity()  # already a string
        access = create_access_token(identity=identity)
        return jsonify({"access_token": access})

    return _do()

