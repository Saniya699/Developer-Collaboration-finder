import os
from typing import Any

from flask import Flask, jsonify, make_response
from flask_jwt_extended.exceptions import JWTExtendedException

from .config import Config
from .extensions import bcrypt, db, jwt, create_socketio


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Ensure the JWT subject/identity is always encoded as a string.
    # Some JWT validators are strict about `sub` being a string.
    @jwt.user_identity_loader
    def user_identity_loader_callback(identity):
        return str(identity) if identity is not None else ""

    # Basic CORS headers for local development and simple deployment.
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = app.config.get("FRONTEND_ORIGIN", "*")
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    from .routes.auth import auth_bp
    from .routes.profile import profile_bp
    from .routes.projects import projects_bp
    from .routes.matching import matching_bp
    from .routes.chat import chat_bp
    from .routes.notifications import notifications_bp
    from .routes.ratings import ratings_bp
    from .routes.resume import resume_bp
    from .routes.search import search_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(matching_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(ratings_bp, url_prefix="/api")
    app.register_blueprint(resume_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")

    # Healthcheck (useful for deployment readiness probes).
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    # JWT error handlers.
    @jwt.unauthorized_loader
    def unauthorized_loader(reason: str):
        return make_response(jsonify({"message": "Missing or invalid JWT", "reason": reason}), 401)

    @jwt.invalid_token_loader
    def invalid_token_loader(reason: str):
        return make_response(jsonify({"message": "Invalid JWT", "reason": reason}), 422)

    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        return make_response(jsonify({"message": "JWT expired", "reason": "token_expired"}), 401)

    # Generic JSON error handler for common exceptions.
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_extended_exception(e: JWTExtendedException):
        return make_response(jsonify({"message": "JWT error", "reason": str(e)}), 401)

    # Register SocketIO event handlers.
    from .sockets import register_socketio_handlers

    app.socketio = create_socketio(app)  # type: ignore[attr-defined]
    register_socketio_handlers(app.socketio)  # type: ignore[attr-defined]

    return app

