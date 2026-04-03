from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..config import Config
from ..models import AvailabilityLevel, ExperienceLevel, Project, ProjectStatus, User


EXPERIENCE_RANK = {
    ExperienceLevel.BEGINNER.value: 0,
    ExperienceLevel.INTERMEDIATE.value: 1,
    ExperienceLevel.ADVANCED.value: 2,
}

AVAILABILITY_SCORE = {
    (AvailabilityLevel.PART_TIME.value, AvailabilityLevel.PART_TIME.value): 1.0,
    (AvailabilityLevel.FULL_TIME.value, AvailabilityLevel.FULL_TIME.value): 1.0,
    (AvailabilityLevel.PART_TIME.value, AvailabilityLevel.FULL_TIME.value): 0.5,
    (AvailabilityLevel.FULL_TIME.value, AvailabilityLevel.PART_TIME.value): 0.5,
}


def _exp_compat(a: str, b: str) -> float:
    # a/b are experience levels
    ra = EXPERIENCE_RANK.get(a, 0)
    rb = EXPERIENCE_RANK.get(b, 0)
    diff = abs(ra - rb)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.66
    return 0.33


def _availability_compat(a: str, b: str) -> float:
    return AVAILABILITY_SCORE.get((a, b), 0.5)


@dataclass(frozen=True)
class MatchScore:
    overall: float
    skill_similarity: float
    experience_compatibility: float
    availability_compatibility: float


def _get_skill_index_map(skill_names: Sequence[str]) -> Dict[str, int]:
    # Normalize with lowercase for robust matching.
    return {name.strip().lower(): i for i, name in enumerate(skill_names)}


def _vectorize_binary(skills: Iterable[str], skill_index_map: Dict[str, int]) -> np.ndarray:
    vec = np.zeros(len(skill_index_map), dtype=np.int8)
    for s in skills or []:
        if not isinstance(s, str):
            continue
        key = s.strip().lower()
        idx = skill_index_map.get(key)
        if idx is not None:
            vec[idx] = 1
    return vec


def _cosine_sim(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    if vec_a.sum() == 0 or vec_b.sum() == 0:
        return 0.0
    # sklearn expects 2D arrays
    sim = cosine_similarity([vec_a], [vec_b])[0][0]
    if np.isnan(sim):
        return 0.0
    return float(sim)


def score_match(
    skill_similarity: float, experience_compatibility: float, availability_compatibility: float
) -> MatchScore:
    w = Config.MATCH_WEIGHTS
    overall = w["skill"] * skill_similarity + w["experience"] * experience_compatibility + w["availability"] * availability_compatibility
    return MatchScore(
        overall=float(overall),
        skill_similarity=float(skill_similarity),
        experience_compatibility=float(experience_compatibility),
        availability_compatibility=float(availability_compatibility),
    )


def skill_gap(user_skills: Sequence[str], project_required_skills: Sequence[str]) -> Dict[str, List[str]]:
    user_set = {s.strip().lower() for s in user_skills or [] if isinstance(s, str) and s.strip()}
    required = [s for s in project_required_skills or [] if isinstance(s, str) and s.strip()]
    missing = []
    matched = []
    for s in required:
        key = s.strip().lower()
        if key in user_set:
            matched.append(s)
        else:
            missing.append(s)
    return {"missing_skills": missing, "matched_skills": matched}

