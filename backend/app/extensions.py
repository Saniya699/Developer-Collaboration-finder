from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_socketio(app):
    # Use threading mode to keep local/dev installs simple.
    return SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
    )

