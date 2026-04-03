from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_socketio(app):
    # Use env-configurable async mode:
    # - local default: threading
    # - Render/prod: eventlet
    return SocketIO(
        app,
        cors_allowed_origins=app.config.get("FRONTEND_ORIGIN", "*"),
        async_mode=app.config.get("SOCKETIO_ASYNC_MODE", "threading"),
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
    )

