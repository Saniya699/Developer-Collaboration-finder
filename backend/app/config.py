import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.environ.get("DEBUG", "0") == "1"
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

    # Database
    # SQLite for local/offline by default.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///dev_developer_collaboration_finder.sqlite3",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    # Flask-JWT-Extended defaults the identity claim to `sub` which some JWT validators
    # require to be a string. Store identity under a custom claim instead.
    JWT_IDENTITY_CLAIM = os.environ.get("JWT_IDENTITY_CLAIM", "identity")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_MINUTES", str(60 * 24)))
    )

    # Uploads (local-only)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    RESUME_MAX_FILE_BYTES = int(os.environ.get("RESUME_MAX_FILE_BYTES", str(8 * 1024 * 1024)))  # 8MB

    # SocketIO
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("SOCKETIO_MESSAGE_QUEUE")  # optional for multi-worker
    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")

    # Matching
    MATCH_WEIGHTS = {
        "skill": float(os.environ.get("MATCH_WEIGHT_SKILL", "0.7")),
        "experience": float(os.environ.get("MATCH_WEIGHT_EXPERIENCE", "0.15")),
        "availability": float(os.environ.get("MATCH_WEIGHT_AVAILABILITY", "0.15")),
    }

    # Seed skills for an initial global skill list.
    SEED_SKILLS = [
        "Python",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "Flask",
        "Django",
        "SQL",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Machine Learning",
        "Scikit-learn",
        "Docker",
        "Kubernetes",
        "Git",
        "HTML",
        "CSS",
        "Tailwind CSS",
        "REST",
        "GraphQL",
    ]

