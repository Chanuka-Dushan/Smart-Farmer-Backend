import os
import sys
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List

import joblib
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.part import Part
from utils.vectorizer.text_builder import build_part_text


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
ARTIFACTS_DIR = os.path.join(BACKEND_DIR, "models_artifacts")

TFIDF_PATH = os.path.join(ARTIFACTS_DIR, "tfidf.joblib")

_tfidf = None


def _load_tfidf():
    global _tfidf
    if _tfidf is None:
        _tfidf = joblib.load(TFIDF_PATH)
    return _tfidf


def build_search_query_text(query: str) -> str:
    """
    Clean search query:
    - lowercase
    - keep letters/numbers/spaces
    - remove extra spaces
    """
    query = (query or "").strip().lower()
    query = re.sub(r"[^a-z0-9\s\.]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query


def normalize_token_text(text: str) -> str:
    """
    Normalize text for machine model matching.
    Example:
    'MF 240' -> 'mf240'
    'TAFE 45 DI' -> 'tafe45di'
    """
    text = build_search_query_text(text)
    return text.replace(" ", "")


def fuzzy_score(query: str, part: Part) -> float:
    """
    Typo-tolerant fuzzy score using multiple views of part text.
    """
    query_text = build_search_query_text(query)

    name_text = build_search_query_text(part.name or "")
    model_text = build_search_query_text(part.machine_model or "")
    category_text = build_search_query_text(part.category or "")
    combined = build_search_query_text(
        f"{part.name or ''} {part.machine_model or ''} {part.category or ''}"
    )

    score_name = SequenceMatcher(None, query_text, name_text).ratio()
    score_model = SequenceMatcher(None, query_text, model_text).ratio()
    score_category = SequenceMatcher(None, query_text, category_text).ratio()
    score_combined = SequenceMatcher(None, query_text, combined).ratio()

    return max(score_name, score_model, score_category, score_combined)


def model_hint_score(query: str, part: Part) -> float:
    """
    Give small boost when machine model hints from query match part.machine_model.
    Handles forms like:
    mf240 <-> mf 240
    tafe45di <-> tafe 45 di
    """
    query_norm = normalize_token_text(query)
    model_norm = normalize_token_text(part.machine_model or "")

    hints = [
        "mf240",
        "tafe7250",
        "tafe45di",
        "kubota4508",
        "tafe",
        "kubota",
        "mf",
    ]

    for hint in hints:
        if hint in query_norm and hint in model_norm:
            return 1.0

    return 0.0


def token_overlap_score(query: str, part: Part) -> float:
    """
    Boost score when important query words overlap with part text.
    """
    query_tokens = set(build_search_query_text(query).split())
    part_tokens = set(
        build_search_query_text(
            f"{part.name or ''} {part.category or ''} {part.machine_model or ''}"
        ).split()
    )

    if not query_tokens or not part_tokens:
        return 0.0

    overlap = query_tokens.intersection(part_tokens)
    return len(overlap) / max(len(query_tokens), 1)


def search_parts(db: Session, query: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Semantic + typo-tolerant search using:
    - TF-IDF cosine similarity
    - fuzzy score
    - token overlap
    - machine model hint
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    tfidf = _load_tfidf()

    query_text = build_search_query_text(query)
    query_vector = tfidf.transform([query_text])

    parts = db.query(Part).all()

    results: List[Dict[str, Any]] = []

    for part in parts:
        part_text = build_part_text(part)
        part_vector = tfidf.transform([part_text])

        semantic_score = float(cosine_similarity(query_vector, part_vector)[0][0])
        fuzzy = fuzzy_score(query, part)
        overlap = token_overlap_score(query, part)
        hint = model_hint_score(query, part)

        final_search_score = (
            0.70 * semantic_score +
            0.15 * fuzzy +
            0.10 * overlap +
            0.05 * hint
        )

        results.append({
            "part_id": part.id,
            "name": part.name,
            "brand": part.brand,
            "machine_model": part.machine_model,
            "category": part.category,
            "compatibility_group": getattr(part, "compatibility_group", None),
            "search_score": round(final_search_score, 4),
            "semantic_score": round(semantic_score, 4),
            "fuzzy_score": round(fuzzy, 4),
            "token_overlap_score": round(overlap, 4),
            "model_hint_score": round(hint, 4),
        })

    results.sort(key=lambda x: x["search_score"], reverse=True)

    return {
        "query": query,
        "normalized_query": query_text,
        "total_results": len(results[:top_k]),
        "results": results[:top_k]
    }