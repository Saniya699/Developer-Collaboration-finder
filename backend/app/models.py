import enum
from datetime import datetime
from typing import Iterable, List, Optional

from flask_bcrypt import generate_password_hash
from flask_jwt_extended import get_jwt_identity

from .extensions import bcrypt, db


class ExperienceLevel(str, enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class AvailabilityLevel(str, enum.Enum):
    PART_TIME = "Part-time"
    FULL_TIME = "Full-time"


class ProjectStatus(str, enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class NotificationType(str, enum.Enum):
    APPLICATION_CREATED = "application_created"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"
    MESSAGE_RECEIVED = "message_received"
    RATING_CREATED = "rating_created"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    bio = db.Column(db.Text, default="")
    # JSON list of skill names
    skills = db.Column(db.JSON, default=list)

    experience_level = db.Column(db.String(32), nullable=False, default=ExperienceLevel.BEGINNER.value)
    availability = db.Column(db.String(32), nullable=False, default=AvailabilityLevel.PART_TIME.value)
    github_url = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ratings_received = db.relationship("Rating", foreign_keys="Rating.to_user_id", back_populates="to_user")
    ratings_given = db.relationship("Rating", foreign_keys="Rating.from_user_id", back_populates="from_user")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def rating_average(self) -> Optional[float]:
        avg = db.session.query(db.func.avg(Rating.score)).filter(Rating.to_user_id == self.id).scalar()
        if avg is None:
            return None
        return round(float(avg), 2)

    @staticmethod
    def normalize_skill_list(skills: Iterable[str]) -> List[str]:
        cleaned = []
        for s in skills or []:
            if not isinstance(s, str):
                continue
            ss = s.strip()
            if ss:
                cleaned.append(ss)
        # De-dupe while preserving order.
        seen = set()
        out = []
        for s in cleaned:
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    @staticmethod
    def ensure_global_skills(skill_names: Iterable[str]) -> None:
        # Create missing global skills locally (no external APIs).
        names = User.normalize_skill_list(skill_names)
        if not names:
            return
        existing = {s.name.lower(): s for s in Skill.query.filter(db.func.lower(Skill.name).in_([n.lower() for n in names])).all()}  # type: ignore
        for name in names:
            key = name.lower()
            if key in existing:
                continue
            db.session.add(Skill(name=name))


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, default="")

    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    creator = db.relationship("User")

    required_skills = db.Column(db.JSON, default=list)  # JSON list of skill names
    max_team_size = db.Column(db.Integer, nullable=False, default=5)
    status = db.Column(db.String(16), nullable=False, default=ProjectStatus.OPEN.value)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship("ProjectMember", back_populates="project", cascade="all,delete-orphan")
    applications = db.relationship("Application", back_populates="project", cascade="all,delete-orphan")

    def member_user_ids(self) -> List[int]:
        return [m.user_id for m in self.members]


class ProjectMember(db.Model):
    __tablename__ = "project_members"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", back_populates="members")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    status = db.Column(db.String(16), nullable=False, default=ApplicationStatus.PENDING.value, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decision_at = db.Column(db.DateTime, nullable=True)

    # Optional: an applicant can add a brief note.
    message = db.Column(db.Text, default="")

    project = db.relationship("Project", back_populates="applications")
    applicant = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("project_id", "applicant_id", name="uq_project_applicant"),
        db.Index("ix_applications_project_status", "project_id", "status"),
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    # If it's a direct message, store recipient_user_id; for project chat, store project_id.
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True, index=True)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_user_id])
    project = db.relationship("Project")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(64), nullable=False, index=True)
    payload = db.Column(db.JSON, default=dict)

    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True, index=True)

    score = db.Column(db.Integer, nullable=False)  # 1-5
    feedback = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    from_user = db.relationship("User", foreign_keys=[from_user_id], back_populates="ratings_given")
    to_user = db.relationship("User", foreign_keys=[to_user_id], back_populates="ratings_received")

    __table_args__ = (
        db.UniqueConstraint("from_user_id", "to_user_id", "project_id", name="uq_rating_per_project"),
        db.Index("ix_ratings_to_user", "to_user_id"),
    )


def seed_skills_if_needed() -> None:
    # Seed a baseline skill universe so matching + resume parsing works early.
    from .config import Config

    existing = {s.name.lower() for s in Skill.query.all()}
    for name in Config.SEED_SKILLS:
        if name.lower() in existing:
            continue
        db.session.add(Skill(name=name))

