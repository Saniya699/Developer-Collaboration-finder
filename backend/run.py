import os

from app import create_app
from app.extensions import create_socketio
from app.models import seed_skills_if_needed
from app.extensions import db
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    app = create_app()
    socketio = getattr(app, "socketio", None) or create_socketio(app)

    with app.app_context():
        db.create_all()
        seed_skills_if_needed()

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = bool(app.config.get("DEBUG", False))

    # Local/offline dev mode: Werkzeug is acceptable. For production use a proper server.
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()

