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
from utils.vectorizer.vector_cache import get_part_vector, get_vectors_by_part_ids


def get_feedback_score(query_part_id: int, candidate_part_id: int, db: Session) -> float:
    """
    Placeholder for future feedback learning.
    For now always return 0.0
    """
    return 0.0


def filter_candidate_parts(db: Session, query_part: Part) -> List[Part]:
    """
    Cross-brand rule filtering:
    - same category
    - same compatibility_group
    - exclude query part itself
    """
    candidates = (
        db.query(Part)
        .filter(Part.id != query_part.id)
        .filter(Part.category == query_part.category)
        .filter(Part.compatibility_group == query_part.compatibility_group)
        .all()
    )
    return candidates


def build_explanation(query_part: Part, candidate_part: Part, vector_similarity_score: float) -> List[str]:
    explanation = []

    if query_part.category == candidate_part.category:
        explanation.append("Same category matched")

    if query_part.compatibility_group == candidate_part.compatibility_group:
        explanation.append("Same compatibility group matched")

    # Strong item-level clue
    if query_part.name and candidate_part.name:
        if query_part.name.strip().lower() == candidate_part.name.strip().lower():
            explanation.append("Exact part name matched")

    if vector_similarity_score >= 0.70:
        explanation.append("Text/spec similarity is high")
    elif vector_similarity_score >= 0.40:
        explanation.append("Text/spec similarity is moderate")

    try:
        if query_part.diameter is not None and candidate_part.diameter is not None:
            diff = abs(float(query_part.diameter) - float(candidate_part.diameter))
            if diff <= 2:
                explanation.append("Similar diameter")
    except Exception:
        pass

    explanation.append("Feedback learning contribution currently set to 0.0")

    return explanation


def recommend_parts(db: Session, part_id: int, top_k: int = 5) -> Dict[str, Any]:
    """
    Main recommendation pipeline:
    1. Fetch query part
    2. Filter candidates by category + compatibility_group
    3. Fetch cached vectors
    4. Compute cosine similarity
    5. hybrid_score = vector_similarity
    6. feedback_score = 0.0
    7. final_score = 0.90 * hybrid_score + 0.10 * feedback_score
    8. Rank by final score
    """
    # Step 1 - get query part
    query_part = db.query(Part).filter(Part.id == part_id).first()
    if not query_part:
        raise ValueError(f"Part with id {part_id} not found")

    # Guard: compatibility_group should exist for cross-brand logic
    if not getattr(query_part, "compatibility_group", None):
        raise ValueError(
            f"Part id {part_id} does not have compatibility_group. "
            f"Cross-brand recommendation needs compatibility_group."
        )

    # Step 2 - get query vector
    query_vector = get_part_vector(db, query_part.id)
    if query_vector is None:
        raise ValueError(f"No cached vector found for part id {part_id}")

    # Step 3 - filter candidates
    candidates = filter_candidate_parts(db, query_part)

    # Step 4 - fetch candidate vectors
    candidate_ids = [candidate.id for candidate in candidates]
    candidate_vectors_map = get_vectors_by_part_ids(db, candidate_ids)

    results = []
    query_vector_np = np.array(query_vector).reshape(1, -1)

    # Step 5 - compute scores
    for candidate in candidates:
        candidate_vector = candidate_vectors_map.get(candidate.id)

        # skip missing cached vectors
        if candidate_vector is None:
            continue

        candidate_vector_np = np.array(candidate_vector).reshape(1, -1)

        vector_similarity_score = float(
            cosine_similarity(query_vector_np, candidate_vector_np)[0][0]
        )

        # Current hybrid score choice
        hybrid_score = vector_similarity_score

        # Future-ready feedback placeholder
        feedback_score = get_feedback_score(query_part.id, candidate.id, db)

        # Final score formula
        final_score = 0.90 * hybrid_score + 0.10 * feedback_score

        explanation = build_explanation(
            query_part=query_part,
            candidate_part=candidate,
            vector_similarity_score=vector_similarity_score
        )

        results.append({
            "recommended_part": candidate.id,
            "name": candidate.name,
            "category": candidate.category,
            "machine_model": candidate.machine_model,
            "compatibility_group": candidate.compatibility_group,
            "hybrid_score": round(hybrid_score, 4),
            "feedback_score": round(feedback_score, 4),
            "final_score": round(final_score, 4),
            "similarity_percentage": round(final_score * 100, 2),
            "explanation": explanation
        })

    # Step 6 - rank by final score
    results.sort(key=lambda x: x["final_score"], reverse=True)

    return {
        "query_part": {
            "id": query_part.id,
            "name": query_part.name,
            "category": query_part.category,
            "machine_model": query_part.machine_model,
            "compatibility_group": query_part.compatibility_group
        },
        "total_candidates": len(candidates),
        "recommendations": results[:top_k]
    }