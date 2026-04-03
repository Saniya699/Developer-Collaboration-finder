import pytest

from app.extensions import db
from app.models import AvailabilityLevel, ExperienceLevel, ProjectStatus


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client, email, password="password123", name="User"):
    reg = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "skills": ["Python", "Flask"],
            "experience_level": ExperienceLevel.BEGINNER.value,
            "availability": AvailabilityLevel.PART_TIME.value,
        },
    )
    assert reg.status_code in (201, 409)

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    data = login.get_json()
    return data["access_token"]


def test_auth_and_profile_update(client):
    token = register_and_login(client, "t1@example.com", name="T1")

    me = client.get("/api/profile/me", headers=auth_headers(token))
    assert me.status_code == 200

    upd = client.put(
        "/api/profile",
        headers=auth_headers(token),
        json={
            "bio": "Updated bio",
            "skills": ["Python", "React"],
            "experience_level": ExperienceLevel.INTERMEDIATE.value,
            "availability": AvailabilityLevel.FULL_TIME.value,
        },
    )
    assert upd.status_code == 200


def test_project_create_apply_and_decision(client):
    creator_token = register_and_login(client, "creator@example.com", name="Creator")
    applicant_token = register_and_login(client, "applicant@example.com", name="Applicant")

    # Create project
    proj = client.post(
        "/api/projects",
        headers=auth_headers(creator_token),
        json={
            "title": "Test Project",
            "description": "Local collaboration test",
            "required_skills": ["Python", "React"],
            "max_team_size": 2,
            "status": ProjectStatus.OPEN.value,
        },
    )
    assert proj.status_code == 201
    project_id = proj.get_json()["project"]["id"]

    # Apply
    app = client.post(f"/api/projects/{project_id}/apply", headers=auth_headers(applicant_token), json={"message": "Hi!"})
    assert app.status_code in (201, 409)

    # Decide (accept)
    # Fetch applications to get applicant_id (should be stable but query anyway).
    apps = client.get(f"/api/projects/{project_id}/applications", headers=auth_headers(creator_token))
    assert apps.status_code == 200
    items = apps.get_json()["items"]
    assert len(items) >= 1
    applicant_id = items[0]["applicant_id"]

    decision = client.post(
        f"/api/projects/{project_id}/applications/{applicant_id}/decision",
        headers=auth_headers(creator_token),
        json={"decision": "accept"},
    )
    assert decision.status_code == 200


def test_matching_endpoints_return_results(client):
    token = register_and_login(client, "m1@example.com", name="M1")
    # Create another user to match.
    register_and_login(client, "m2@example.com", name="M2")

    res_teammates = client.get("/api/matches/teammates?top=5", headers=auth_headers(token))
    assert res_teammates.status_code == 200

    res_projects = client.get("/api/matches/projects?top=5&status=Open", headers=auth_headers(token))
    assert res_projects.status_code == 200

