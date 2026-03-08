import os
import sys
from typing import Dict, Any, List

import numpy as np
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.part import Part
from utils.vectorizer.vector_cache import get_part_vector
from utils.vectorizer.recommender import get_feedback_score, build_explanation


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def compute_pair_scores(
    db: Session,
    original_part: Part,
    alternative_part: Part
) -> Dict[str, float]:
    """
    Compute recommender scores between two specific parts.
    Reuses the same logic as recommender:
    hybrid_score = vector_similarity
    feedback_score = 0.0
    final_score = 0.90 * hybrid_score + 0.10 * feedback_score
    """
    original_vector = get_part_vector(db, original_part.id)
    alternative_vector = get_part_vector(db, alternative_part.id)

    if original_vector is None:
        raise ValueError(f"No cached vector found for original part id {original_part.id}")

    if alternative_vector is None:
        raise ValueError(f"No cached vector found for alternative part id {alternative_part.id}")

    original_np = np.array(original_vector).reshape(1, -1)
    alternative_np = np.array(alternative_vector).reshape(1, -1)

    vector_similarity = float(cosine_similarity(original_np, alternative_np)[0][0])

    hybrid_score = vector_similarity
    feedback_score = get_feedback_score(original_part.id, alternative_part.id, db)
    final_score = 0.90 * hybrid_score + 0.10 * feedback_score

    return {
        "hybrid_score": round(hybrid_score, 4),
        "feedback_score": round(feedback_score, 4),
        "final_score": round(final_score, 4),
        "similarity_percentage": round(final_score * 100, 2)
    }


def build_comparison_summary(original_part: Part, alternative_part: Part) -> Dict[str, Any]:
    """
    Build field-by-field comparison summary for frontend comparison view.
    """
    original_diameter = _safe_float(getattr(original_part, "diameter", None))
    alternative_diameter = _safe_float(getattr(alternative_part, "diameter", None))

    original_price = _safe_float(getattr(original_part, "price", None))
    alternative_price = _safe_float(getattr(alternative_part, "price", None))

    same_category = original_part.category == alternative_part.category
    same_compatibility_group = (
        getattr(original_part, "compatibility_group", None) ==
        getattr(alternative_part, "compatibility_group", None)
    )
    same_name = (original_part.name or "").strip().lower() == (alternative_part.name or "").strip().lower()

    price_difference = None
    if original_price is not None and alternative_price is not None:
        price_difference = round(alternative_price - original_price, 2)

    diameter_difference = None
    if original_diameter is not None and alternative_diameter is not None:
        diameter_difference = round(alternative_diameter - original_diameter, 2)

    material_match = None
    if getattr(original_part, "material", None) or getattr(alternative_part, "material", None):
        material_match = (original_part.material or "").strip().lower() == (alternative_part.material or "").strip().lower()

    return {
        "same_category": same_category,
        "same_compatibility_group": same_compatibility_group,
        "same_name": same_name,
        "price_difference": price_difference,
        "diameter_difference": diameter_difference,
        "material_match": material_match
    }


def serialize_part(part: Part) -> Dict[str, Any]:
    return {
        "id": part.id,
        "name": part.name,
        "brand": part.brand,
        "machine_model": part.machine_model,
        "category": part.category,
        "price": part.price,
        "diameter": part.diameter,
        "material": part.material,
        "compatibility_group": getattr(part, "compatibility_group", None),
        "description": part.description,
        "specs_json": part.specs_json,
        "image_url": part.image_url
    }


def compare_parts(
    db: Session,
    original_part_id: int,
    alternative_part_id: int
) -> Dict[str, Any]:
    """
    Main comparison endpoint logic.
    """
    original_part = db.query(Part).filter(Part.id == original_part_id).first()
    if not original_part:
        raise ValueError(f"Original part with id {original_part_id} not found")

    alternative_part = db.query(Part).filter(Part.id == alternative_part_id).first()
    if not alternative_part:
        raise ValueError(f"Alternative part with id {alternative_part_id} not found")

    comparison = build_comparison_summary(original_part, alternative_part)

    if not comparison["same_compatibility_group"]:
        compatibility_reason = "These parts are not in the same compatibility group"
    else:
        compatibility_reason = "These parts belong to the same compatibility group"

    scores = compute_pair_scores(db, original_part, alternative_part)

    explanation = build_explanation(
        query_part=original_part,
        candidate_part=alternative_part,
        vector_similarity_score=scores["hybrid_score"]
    )

    return {
        "original_part": serialize_part(original_part),
        "alternative_part": serialize_part(alternative_part),
        "comparison": comparison,
        "compatibility_reason": compatibility_reason,
        "recommendation_scores": scores,
        "explanation": explanation
    }