"""
Production entrypoint for WSGI servers (Render/Gunicorn).
"""

from dotenv import load_dotenv

from app import create_app
from app.extensions import db
from app.models import seed_skills_if_needed

load_dotenv()

app = create_app()

with app.app_context():
    db.create_all()
    seed_skills_if_needed()

