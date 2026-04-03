from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import Notification
from ..extensions import db


notifications_bp = Blueprint("notifications_bp", __name__)


@notifications_bp.get("/notifications")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    items = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": n.id,
                    "type": n.type,
                    "payload": n.payload or {},
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in items
            ]
        }
    )


@notifications_bp.post("/notifications/<int:notification_id>/read")
@jwt_required()
def mark_read(notification_id: int):
    user_id = int(get_jwt_identity())
    n = Notification.query.get(notification_id)
    if not n or n.user_id != user_id:
        return jsonify({"message": "notification not found"}), 404
    n.read_at = db.func.now()
    db.session.commit()
    return jsonify({"message": "notification marked as read"}), 200

