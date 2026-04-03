from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Notification, NotificationType, Rating, User


ratings_bp = Blueprint("ratings_bp", __name__)


@ratings_bp.post("/ratings")
@jwt_required()
def create_rating():
    data = request.get_json(silent=True) or {}
    from_user_id = int(get_jwt_identity())

    to_user_id = int(data.get("to_user_id") or 0)
    project_id = data.get("project_id", None)
    score = int(data.get("score") or 0)
    feedback = (data.get("feedback") or "").strip()

    if not to_user_id:
        return jsonify({"message": "to_user_id is required"}), 400
    if to_user_id == from_user_id:
        return jsonify({"message": "cannot rate yourself"}), 400
    if score < 1 or score > 5:
        return jsonify({"message": "score must be between 1 and 5"}), 400

    to_user = User.query.get(to_user_id)
    if not to_user:
        return jsonify({"message": "to_user not found"}), 404

    project_id_int = int(project_id) if project_id is not None else None

    rating = Rating.query.filter_by(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        project_id=project_id_int,
    ).first()

    if rating:
        rating.score = score
        rating.feedback = feedback
    else:
        rating = Rating(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            project_id=project_id_int,
            score=score,
            feedback=feedback,
        )
        db.session.add(rating)

    # Notify recipient about a new rating.
    db.session.add(
        Notification(
            user_id=to_user_id,
            type=NotificationType.RATING_CREATED.value,
            payload={
                "from_user_id": from_user_id,
                "project_id": project_id_int,
                "score": score,
            },
        )
    )
    db.session.commit()

    return (
        jsonify(
            {
                "message": "rating saved",
                "rating": {
                    "id": rating.id,
                    "from_user_id": rating.from_user_id,
                    "to_user_id": rating.to_user_id,
                    "project_id": rating.project_id,
                    "score": rating.score,
                    "feedback": rating.feedback,
                    "created_at": rating.created_at.isoformat() if rating.created_at else None,
                },
                "to_user_rating_avg": to_user.rating_average(),
            }
        ),
        201,
    )


@ratings_bp.get("/ratings/user/<int:user_id>")
@jwt_required()
def list_ratings_for_user(user_id: int):
    to_user = User.query.get(user_id)
    if not to_user:
        return jsonify({"message": "user not found"}), 404

    items = (
        Rating.query.filter_by(to_user_id=user_id)
        .order_by(Rating.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        {
            "user": {"id": to_user.id, "name": to_user.name, "profile_rating_avg": to_user.rating_average()},
            "items": [
                {
                    "id": r.id,
                    "from_user_id": r.from_user_id,
                    "project_id": r.project_id,
                    "score": r.score,
                    "feedback": r.feedback,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in items
            ],
        }
    )

