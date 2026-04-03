import os
import tempfile

import pytest

import sys

# Ensure the backend root is on sys.path so `import app` works under pytest.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app import create_app
from app.extensions import db
from app.models import seed_skills_if_needed


@pytest.fixture(scope="session")
def app():
    # Use a temp sqlite file so multiple requests work during a test session.
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)

    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{path}",
        JWT_SECRET_KEY="test-jwt-secret",
        SECRET_KEY="test-secret",
    )

    with app.app_context():
        db.create_all()
        seed_skills_if_needed()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()

