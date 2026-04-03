from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required


chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.get("/chat/conversations")
@jwt_required()
def conversations_stub():
    from ..extensions import db
    from ..models import Message, ProjectMember, Project, User

    me = int(get_jwt_identity())

    # Direct conversations (based on existing stored messages).
    msg_q = Message.query.filter(
        ((Message.sender_id == me) & (Message.recipient_user_id.isnot(None)))
        | (Message.recipient_user_id == me)
    ).order_by(Message.created_at.desc())
    rows = msg_q.limit(200).all()

    latest_by_other = {}
    for m in rows:
        if m.recipient_user_id is None:
            continue
        other = m.recipient_user_id if m.sender_id == me else m.sender_id
        if other == me:
            continue
        if other not in latest_by_other:
            latest_by_other[other] = m

    direct_items = []
    for other_id, last_msg in latest_by_other.items():
        u = User.query.get(other_id)
        if not u:
            continue
        direct_items.append(
            {
                "type": "direct",
                "other_user": {
                    "id": u.id,
                    "name": u.name,
                    "skills": u.skills or [],
                    "experience_level": u.experience_level,
                    "availability": u.availability,
                    "profile_rating_avg": u.rating_average(),
                },
                "latest_message": {
                    "id": last_msg.id,
                    "sender_id": last_msg.sender_id,
                    "content": last_msg.content,
                    "created_at": last_msg.created_at.isoformat() if last_msg.created_at else None,
                },
            }
        )

    # Project conversations where user is a member.
    project_members = ProjectMember.query.filter_by(user_id=me).all()
    project_items = []
    for pm in project_members:
        p = pm.project
        project_items.append(
            {
                "type": "project",
                "project": {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                },
            }
        )

    return jsonify({"direct": direct_items, "projects": project_items}), 200


@chat_bp.get("/chat/history")
@jwt_required()
def history_stub():
    from ..extensions import db
    from ..models import Message, ProjectMember, Project

    me = int(get_jwt_identity())
    chat_type = (request.args.get("type") or "direct").strip().lower()
    page = int(request.args.get("page") or 1)
    per_page = int(request.args.get("per_page") or 30)

    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({"message": "invalid pagination"}), 400

    if chat_type == "direct":
        other_user_id = request.args.get("other_user_id", type=int)
        if not other_user_id:
            return jsonify({"message": "other_user_id is required"}), 400

        msgs = (
            Message.query.filter(
                (
                    (Message.sender_id == me) & (Message.recipient_user_id == other_user_id)
                )
                | ((Message.sender_id == other_user_id) & (Message.recipient_user_id == me))
            )
        ).order_by(Message.created_at.asc())

        msgs = msgs.offset((page - 1) * per_page).limit(per_page)
        items = [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "recipient_user_id": m.recipient_user_id,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs.all()
        ]
        return jsonify({"items": items}), 200

    if chat_type == "project":
        project_id = request.args.get("project_id", type=int)
        if not project_id:
            return jsonify({"message": "project_id is required"}), 400

        is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=me).first() is not None
        if not is_member:
            return jsonify({"message": "forbidden"}), 403

        msgs = (
            Message.query.filter(
                (Message.project_id == project_id) & (Message.recipient_user_id.is_(None))
            )
        ).order_by(Message.created_at.asc())
        msgs = msgs.offset((page - 1) * per_page).limit(per_page)

        items = [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "project_id": m.project_id,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs.all()
        ]
        return jsonify({"items": items}), 200

    return jsonify({"message": "invalid chat type"}), 400

