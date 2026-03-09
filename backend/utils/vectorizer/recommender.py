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
from utils.feedback_service import get_feedback_score


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


def build_explanation(
    query_part: Part,
    candidate_part: Part,
    vector_similarity_score: float,
    feedback_score: float
) -> List[str]:
    explanation = []

    if query_part.category == candidate_part.category:
        explanation.append("Same category matched")

    if query_part.compatibility_group == candidate_part.compatibility_group:
        explanation.append("Same compatibility group matched")

    if query_part.machine_model == candidate_part.machine_model:
        explanation.append("Same machine model matched")

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

    if feedback_score > 0.60:
        explanation.append("Positive feedback history")
    elif feedback_score < 0.40:
        explanation.append("Negative feedback history")
    else:
        explanation.append("Neutral or limited feedback history")

    return explanation


def recommend_parts(
    db: Session,
    part_id: int,
    top_k: int = 5,
    mode: str = "normal"
) -> Dict[str, Any]:
    """
    Main recommendation pipeline:
    1. Fetch query part
    2. Filter candidates by category + compatibility_group
    3. Fetch cached vectors
    4. Compute cosine similarity
    5. hybrid_score = vector_similarity
    6. feedback_score = get_feedback_score(...)
    7. final_score = 0.90 * hybrid_score + 0.10 * feedback_score
    8. Rank by final score

    mode="normal"       -> returns final ranked recommendations
    mode="before_after" -> returns rankings before and after feedback
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

    before_results = []
    after_results = []

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

        # current hybrid score = vector similarity
        hybrid_score = vector_similarity_score

        # real feedback score from feedback_events
        feedback_score = get_feedback_score(db, query_part.id, candidate.id)

        # final adaptive score
        final_score = 0.90 * hybrid_score + 0.10 * feedback_score

        explanation = build_explanation(
            query_part=query_part,
            candidate_part=candidate,
            vector_similarity_score=vector_similarity_score,
            feedback_score=feedback_score
        )

        # before feedback ranking
        before_results.append({
            "recommended_part": candidate.id,
            "name": candidate.name,
            "category": candidate.category,
            "machine_model": candidate.machine_model,
            "compatibility_group": candidate.compatibility_group,
            "hybrid_score": round(hybrid_score, 4),
            "similarity_percentage": round(hybrid_score * 100, 2)
        })

        # after feedback ranking
        after_results.append({
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

    # sort before feedback by hybrid score only
    before_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

    # sort after feedback by final adaptive score
    after_results.sort(key=lambda x: x["final_score"], reverse=True)

    if mode == "before_after":
        return {
            "query_part": {
                "id": query_part.id,
                "name": query_part.name,
                "category": query_part.category,
                "machine_model": query_part.machine_model,
                "compatibility_group": query_part.compatibility_group
            },
            "total_candidates": len(candidates),
            "before_feedback": before_results[:top_k],
            "after_feedback": after_results[:top_k]
        }

    return {
        "query_part": {
            "id": query_part.id,
            "name": query_part.name,
            "category": query_part.category,
            "machine_model": query_part.machine_model,
            "compatibility_group": query_part.compatibility_group
        },
        "total_candidates": len(candidates),
        "recommendations": after_results[:top_k]
    }