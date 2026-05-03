import os
import sys
from typing import List, Dict, Any

import numpy as np
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.part import Part
from models.research import FeedbackEvent
from utils.vectorizer.vector_cache import get_part_vector, get_vectors_by_part_ids
from utils.feedback_service import get_feedback_score
from utils.ml.rf_predictor import predict_rf_probability


# ---------------- HARD FILTER ----------------
def filter_candidate_parts(db: Session, query_part: Part) -> List[Part]:
    """
    Phase 3:
    Hard rules are used only for filtering, not scoring.

    Required:
    - exclude same exact part
    - same category
    - same machine_family
    - same compatibility_group
    - same function_type
    """

    candidates = (
        db.query(Part)
        .filter(Part.id != query_part.id)
        .filter(Part.category == query_part.category)
        .filter(Part.machine_family == query_part.machine_family)
        .filter(Part.compatibility_group == query_part.compatibility_group)
        .filter(Part.function_type == query_part.function_type)
        .all()
    )

    return candidates


# ---------------- SUBSTITUTE LEVEL ----------------
def get_substitute_level(final_score: float) -> str:
    if final_score >= 0.85:
        return "exact"
    elif final_score >= 0.70:
        return "near"
    return "functional"


# ---------------- DATA QUALITY ----------------
def calculate_data_quality_score(part: Part) -> float:
    fields = [
        part.name,
        part.category,
        part.machine_model,
        part.machine_family,
        part.function_type,
        part.compatibility_group,
        part.price,
        part.lifespan,
        part.specs_json,
    ]

    filled = sum(1 for v in fields if v not in [None, "", 0])
    return filled / len(fields)


# ---------------- FEEDBACK RELIABILITY ----------------
def calculate_feedback_reliability_score(db: Session, part_id: int, rec_id: int) -> float:
    count = db.query(FeedbackEvent).filter(
        FeedbackEvent.part_id == part_id,
        FeedbackEvent.recommended_part_id == rec_id
    ).count()

    if count >= 5:
        return 1.0
    elif count >= 2:
        return 0.75
    elif count == 1:
        return 0.60
    return 0.50


# ---------------- CONFIDENCE ----------------
def calculate_confidence_score(ml: float, dq: float, fr: float) -> float:
    """
    Confidence is kept separate from final_score.
    """
    score = 0.60 * ml + 0.25 * dq + 0.15 * fr
    return min(max(score, 0), 1)


# ---------------- EVIDENCE SOURCE ----------------
def get_evidence_source(ml_score: float, feedback_score: float) -> str:
    if feedback_score > 0.7:
        return "user_feedback"
    elif ml_score > 0.8:
        return "ml_high_confidence"
    return "system_inferred"


# ---------------- SAFE SPEC HELPER ----------------
def get_spec_value(part: Part, key: str):
    """
    Safely read optional values from specs_json.
    Example keys: diameter, material
    """
    if not part.specs_json:
        return None

    if isinstance(part.specs_json, dict):
        return part.specs_json.get(key)

    return None


# ---------------- DIFFERENCE BUILDER ----------------
def build_differences(query_part: Part, candidate: Part) -> Dict[str, Any]:
    """
    Phase 3:
    Soft rule values are used only for explanation, not final_score.
    Differences are optional because every part does not have every field.
    """

    differences = {}

    # Price difference
    if query_part.price and candidate.price:
        price_diff = candidate.price - query_part.price
        price_percent = (price_diff / query_part.price) * 100

        differences["price"] = {
            "original": query_part.price,
            "recommended": candidate.price,
            "difference": round(price_diff, 2),
            "percentage_difference": round(price_percent, 2),
            "summary": (
                f"Lower price by {abs(round(price_percent, 2))}%"
                if price_diff < 0
                else f"Higher price by {round(price_percent, 2)}%"
                if price_diff > 0
                else "Same price"
            )
        }

    # Lifespan difference
    if query_part.lifespan and candidate.lifespan:
        lifespan_diff = candidate.lifespan - query_part.lifespan

        differences["lifespan"] = {
            "original": query_part.lifespan,
            "recommended": candidate.lifespan,
            "difference": lifespan_diff,
            "summary": (
                "Longer lifespan"
                if lifespan_diff > 0
                else "Shorter lifespan"
                if lifespan_diff < 0
                else "Same lifespan"
            )
        }

    # Optional material from specs_json
    query_material = get_spec_value(query_part, "material")
    candidate_material = get_spec_value(candidate, "material")

    if query_material and candidate_material:
        differences["material"] = {
            "original": query_material,
            "recommended": candidate_material,
            "match": query_material == candidate_material,
            "summary": (
                "Same material"
                if query_material == candidate_material
                else "Different material"
            )
        }

    # Optional diameter from specs_json
    query_diameter = get_spec_value(query_part, "diameter")
    candidate_diameter = get_spec_value(candidate, "diameter")

    if query_diameter and candidate_diameter:
        try:
            diameter_diff = float(candidate_diameter) - float(query_diameter)

            differences["diameter"] = {
                "original": query_diameter,
                "recommended": candidate_diameter,
                "difference": round(diameter_diff, 2),
                "summary": (
                    f"Diameter difference = {abs(round(diameter_diff, 2))} mm"
                    if diameter_diff != 0
                    else "Same diameter"
                )
            }
        except (ValueError, TypeError):
            pass

    return differences


# ---------------- EXPLANATION ----------------
def build_explanation(
    query_part: Part,
    candidate: Part,
    sim: float,
    ml: float,
    feedback: float,
    substitute_level: str,
    confidence: float
) -> Dict[str, Any]:

    matched_fields = {
        "category": query_part.category == candidate.category,
        "machine_family": query_part.machine_family == candidate.machine_family,
        "compatibility_group": query_part.compatibility_group == candidate.compatibility_group,
        "function_type": query_part.function_type == candidate.function_type,
    }

    differences = build_differences(query_part, candidate)

    notes = []

    if all(matched_fields.values()):
        notes.append("Passed all hard compatibility rules")

    if sim >= 0.7:
        notes.append("Vector similarity is high")
    elif sim >= 0.4:
        notes.append("Vector similarity is moderate")
    else:
        notes.append("Vector similarity is low")

    if ml >= 0.7:
        notes.append("Random Forest predicted high compatibility")
    elif ml >= 0.4:
        notes.append("Random Forest predicted moderate compatibility")
    else:
        notes.append("Random Forest predicted low compatibility")

    if feedback >= 0.7:
        notes.append("User feedback strongly supports this recommendation")
    elif feedback >= 0.4:
        notes.append("User feedback moderately supports this recommendation")
    else:
        notes.append("Limited feedback support available")

    if ml > 0.8 and sim > 0.7:
        notes.append("Both ML model and similarity strongly support compatibility")

    if substitute_level == "exact":
        notes.append("This part is a direct replacement candidate")
    elif substitute_level == "near":
        notes.append("This part is a close alternative with minor differences")
    else:
        notes.append("This part is a functional alternative")

    if confidence >= 0.75:
        notes.append("Recommendation confidence is high")
    elif confidence >= 0.5:
        notes.append("Recommendation confidence is moderate")
    else:
        notes.append("Recommendation confidence is low")

    why_recommended = (
        "Recommended because it matches the same category, machine family, "
        "compatibility group, and function type, then ranked using similarity, "
        "Random Forest prediction, and feedback score."
    )

    return {
        "why_recommended": why_recommended,
        "matched_fields": matched_fields,
        "differences": differences,
        "substitute_level": substitute_level,
        "confidence": round(confidence, 4),
        "notes": notes
    }


# ---------------- MAIN RECOMMENDER ----------------
def recommend_parts(db: Session, part_id: int, top_k: int = 5, mode="normal"):

    query = db.query(Part).filter(Part.id == part_id).first()

    if not query:
        return {
            "error": "Part not found",
            "recommendations": []
        }

    query_vec = get_part_vector(db, query.id)

    if not query_vec:
        return {
            "query_part": query.name,
            "total_candidates": 0,
            "recommendations": [],
            "message": "Vector not found for query part"
        }

    query_np = np.array(query_vec).reshape(1, -1)

    candidates = filter_candidate_parts(db, query)

    if not candidates:
        return {
            "query_part": query.name,
            "total_candidates": 0,
            "recommendations": [],
            "message": "No candidates passed the hard compatibility rules"
        }

    vectors = get_vectors_by_part_ids(db, [c.id for c in candidates])

    results = []

    for c in candidates:
        vec = vectors.get(c.id)

        if not vec:
            continue

        sim = float(cosine_similarity(query_np, np.array(vec).reshape(1, -1))[0][0])
        feedback = get_feedback_score(db, query.id, c.id)
        ml = predict_rf_probability(db=db, part_a=query, part_b=c)

        # Keep Phase 2 final score formula unchanged
        final = 0.50 * sim + 0.30 * ml + 0.20 * feedback

        sub = get_substitute_level(final)

        dq = calculate_data_quality_score(c)
        fr = calculate_feedback_reliability_score(db, query.id, c.id)
        conf = calculate_confidence_score(ml, dq, fr)

        evidence = get_evidence_source(ml, feedback)

        explanation = build_explanation(
            query_part=query,
            candidate=c,
            sim=sim,
            ml=ml,
            feedback=feedback,
            substitute_level=sub,
            confidence=conf
        )

        results.append({
            "recommended_part": c.id,
            "name": c.name,
            "category": c.category,
            "machine_family": c.machine_family,
            "compatibility_group": c.compatibility_group,
            "function_type": c.function_type,

            "vector_similarity_score": round(sim, 4),
            "ml_score": round(ml, 4),
            "feedback_score": round(feedback, 4),

            "final_score": round(final, 4),
            "substitute_level": sub,

            "confidence_score": round(conf, 4),
            "data_quality_score": round(dq, 4),
            "feedback_reliability_score": round(fr, 4),
            "evidence_source": evidence,

            "explanation": explanation
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)

    return {
        "query_part": query.name,
        "query_part_id": query.id,
        "hard_filter_rules": [
            "same category",
            "same machine_family",
            "same compatibility_group",
            "same function_type",
            "exclude same exact part"
        ],
        "ranking_formula": "final_score = 0.50 * similarity + 0.30 * ml + 0.20 * feedback",
        "total_candidates": len(results),
        "recommendations": results[:top_k]
    }