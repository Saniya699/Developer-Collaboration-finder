import os

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from pypdf import PdfReader

from ..extensions import db
from ..models import Skill, User
from ..config import Config

resume_bp = Blueprint("resume_bp", __name__)


@resume_bp.post("/resume/analyze")
@jwt_required()
def analyze_resume():
    if "file" not in request.files:
        return jsonify({"message": "missing file field"}), 400

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "user not found"}), 404

    pdf = request.files["file"]
    if not pdf or not pdf.filename:
        return jsonify({"message": "missing file"}), 400

    # Basic validation to keep it local and safe.
    filename = secure_filename(pdf.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext != ".pdf":
        return jsonify({"message": "only PDF files are supported"}), 400

    max_bytes = Config.RESUME_MAX_FILE_BYTES
    if pdf.content_length and pdf.content_length > max_bytes:
        return jsonify({"message": f"file too large (max {max_bytes} bytes)"}), 413

    upload_dir = Config.UPLOAD_FOLDER
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, f"user_{user_id}_{filename}")
    pdf.save(save_path)

    try:
        reader = PdfReader(save_path)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t:
                text_parts.append(t)
        text = "\n".join(text_parts).strip()
    finally:
        # Keep uploads locally for now; you can delete if desired.
        pass

    if not text:
        return jsonify({"message": "could not extract text from PDF"}), 400

    text_lower = text.lower()
    skill_names = [s.name for s in Skill.query.all()]

    found = []
    for name in skill_names:
        n = name.strip()
        if not n:
            continue
        key = n.lower()
        if key in text_lower:
            # Rank matches by frequency (simple heuristic).
            count = text_lower.count(key)
            found.append((n, count))

    found.sort(key=lambda x: x[1], reverse=True)
    suggested = [n for n, _ in found[:50]]

    user_set = {s.strip().lower() for s in (user.skills or []) if isinstance(s, str) and s.strip()}
    suggested_missing = [s for s in suggested if s.strip().lower() not in user_set]

    return (
        jsonify(
            {
                "suggested_skills": suggested,
                "missing_skills_for_profile": suggested_missing,
                "matched_skill_count": len(suggested),
            }
        ),
        200,
    )

