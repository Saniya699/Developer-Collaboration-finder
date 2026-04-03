from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Set

from flask import request as flask_request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from .extensions import db
from .models import Message, Notification, NotificationType, ProjectMember, User


SID_TO_USER: Dict[str, int] = {}
ONLINE_USERS: Set[int] = set()


def _direct_room(a: int, b: int) -> str:
    lo, hi = (a, b) if a < b else (b, a)
    return f"direct:{lo}:{hi}"


def register_socketio_handlers(socketio):
    @socketio.on("connect")
    def on_connect():
        # Authenticate via an explicit "authenticate" event (token is provided by client).
        return None

    @socketio.on("disconnect")
    def on_disconnect():
        user_id = SID_TO_USER.pop(flask_request.sid, None)
        if user_id is None:
            return None
        ONLINE_USERS.discard(user_id)
        # Send presence to the disconnected user only.
        emit("presence_update", {"user_id": user_id, "online": False}, to=f"user:{user_id}")
        return None

    @socketio.on("authenticate")
    def on_authenticate(data):
        token = (data or {}).get("token") or (data or {}).get("access_token")
        if not token:
            return False
        decoded = decode_token(token)
        identity = decoded.get("identity", decoded.get("sub"))
        if identity is None:
            return False
        user_id = int(identity)

        SID_TO_USER[flask_request.sid] = user_id
        ONLINE_USERS.add(user_id)
        join_room(f"user:{user_id}")

        emit("presence_update", {"user_id": user_id, "online": True}, to=f"user:{user_id}")
        return True

    @socketio.on("join_direct")
    def on_join_direct(data):
        other_user_id = (data or {}).get("other_user_id")
        if other_user_id is None:
            return False
        sender_id = SID_TO_USER.get(flask_request.sid)
        if not sender_id:
            return False
        other_user_id = int(other_user_id)
        if other_user_id == sender_id:
            return False
        if not User.query.get(other_user_id):
            return False
        join_room(_direct_room(sender_id, other_user_id))
        return True

    @socketio.on("join_project")
    def on_join_project(data):
        project_id = (data or {}).get("project_id")
        if project_id is None:
            return False
        sender_id = SID_TO_USER.get(flask_request.sid)
        if not sender_id:
            return False
        project_id = int(project_id)
        is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=sender_id).first() is not None
        if not is_member:
            return False
        join_room(f"project:{project_id}")
        return True

    @socketio.on("typing")
    def on_typing(data):
        sender_id = SID_TO_USER.get(flask_request.sid)
        if not sender_id:
            return False

        content = data or {}
        is_typing = bool(content.get("is_typing", True))
        to_user_id = content.get("to_user_id")
        project_id = content.get("project_id")

        if project_id is not None:
            project_id = int(project_id)
            emit(
                "typing",
                {"sender_id": sender_id, "project_id": project_id, "is_typing": is_typing},
                to=f"project:{project_id}",
            )
            return True

        if to_user_id is not None:
            to_user_id = int(to_user_id)
            emit(
                "typing",
                {"sender_id": sender_id, "to_user_id": to_user_id, "is_typing": is_typing},
                to=_direct_room(sender_id, to_user_id),
            )
            return True

        return False

    @socketio.on("send_message")
    def on_send_message(data):
        sender_id = SID_TO_USER.get(flask_request.sid)
        if not sender_id:
            return False

        payload = data or {}
        content = (payload.get("content") or "").strip()
        if not content:
            return False

        to_user_id = payload.get("to_user_id", None)
        project_id = payload.get("project_id", None)

        if project_id is not None and to_user_id is not None:
            return False
        if project_id is None and to_user_id is None:
            return False

        if project_id is not None:
            project_id = int(project_id)
            is_member = ProjectMember.query.filter_by(project_id=project_id, user_id=sender_id).first() is not None
            if not is_member:
                return False

            msg = Message(sender_id=sender_id, recipient_user_id=None, project_id=project_id, content=content)
            db.session.add(msg)
            db.session.commit()

            # Notify all other members in the project.
            other_members = ProjectMember.query.filter_by(project_id=project_id).all()
            for m in other_members:
                if m.user_id == sender_id:
                    continue
                db.session.add(
                    Notification(
                        user_id=m.user_id,
                        type=NotificationType.MESSAGE_RECEIVED.value,
                        payload={"project_id": project_id, "from_user_id": sender_id, "message_id": msg.id},
                    )
                )
            db.session.commit()

            emit(
                "new_message",
                {
                    "id": msg.id,
                    "sender_id": sender_id,
                    "project_id": project_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                },
                to=f"project:{project_id}",
            )
            return True

        # Direct message
        to_user_id = int(to_user_id)
        if not User.query.get(to_user_id):
            return False

        msg = Message(sender_id=sender_id, recipient_user_id=to_user_id, project_id=None, content=content)
        db.session.add(msg)
        db.session.commit()

        # Notify recipient.
        db.session.add(
            Notification(
                user_id=to_user_id,
                type=NotificationType.MESSAGE_RECEIVED.value,
                payload={"from_user_id": sender_id, "message_id": msg.id, "direct": True},
            )
        )
        db.session.commit()

        emit(
            "new_message",
            {
                "id": msg.id,
                "sender_id": sender_id,
                "recipient_user_id": to_user_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "direct": True,
            },
            to=_direct_room(sender_id, to_user_id),
        )
        return True


