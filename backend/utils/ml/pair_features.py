import os
import sys
from typing import Dict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from sqlalchemy.orm import Session
from models.part import Part
from utils.vectorizer.vector_cache import get_part_vector


def safe_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def safe_str(v) -> str:
    if v is None:
        return ""
    return str(v).strip().lower()


def has_valid_number(v) -> bool:
    try:
        if v is None:
            return False
        value = float(v)
        return value > 0
    except (TypeError, ValueError):
        return False


def get_similarity_score(db: Session, part_a: Part, part_b: Part) -> float:
    try:
        vec_a = get_part_vector(db, part_a.id)
        vec_b = get_part_vector(db, part_b.id)

        if vec_a is None or vec_b is None:
            return 0.0

        vec_a_np = np.array(vec_a).reshape(1, -1)
        vec_b_np = np.array(vec_b).reshape(1, -1)

        return float(cosine_similarity(vec_a_np, vec_b_np)[0][0])

    except Exception:
        return 0.0


def build_pair_features(
    db: Session,
    part_a: Part,
    part_b: Part
) -> Dict[str, float]:

    vector_similarity_score = get_similarity_score(db, part_a, part_b)

    diameter_a_valid = has_valid_number(getattr(part_a, "diameter", None))
    diameter_b_valid = has_valid_number(getattr(part_b, "diameter", None))

    diameter_available = int(diameter_a_valid and diameter_b_valid)

    if diameter_available:
        diameter_diff = abs(
            safe_float(getattr(part_a, "diameter", 0))
            - safe_float(getattr(part_b, "diameter", 0))
        )
    else:
        diameter_diff = 0.0

    price_a = safe_float(getattr(part_a, "price", 0))
    price_b = safe_float(getattr(part_b, "price", 0))

    price_diff = abs(price_a - price_b)
    price_ratio = price_a / (price_b + 1)

    lifespan_diff = abs(
        safe_float(getattr(part_a, "lifespan", 0))
        - safe_float(getattr(part_b, "lifespan", 0))
    )

    return {
        "vector_similarity_score": vector_similarity_score,

        "same_category": int(
            safe_str(getattr(part_a, "category", ""))
            == safe_str(getattr(part_b, "category", ""))
        ),

        "same_machine_model": int(
            safe_str(getattr(part_a, "machine_model", ""))
            == safe_str(getattr(part_b, "machine_model", ""))
        ),

        "same_machine_family": int(
            safe_str(getattr(part_a, "machine_family", ""))
            == safe_str(getattr(part_b, "machine_family", ""))
        ),

        "same_function_type": int(
            safe_str(getattr(part_a, "function_type", ""))
            == safe_str(getattr(part_b, "function_type", ""))
        ),

        "same_brand": int(
            safe_str(getattr(part_a, "brand", ""))
            == safe_str(getattr(part_b, "brand", ""))
        ),

        "same_material": int(
            safe_str(getattr(part_a, "material", ""))
            == safe_str(getattr(part_b, "material", ""))
        ),

        "price_diff": price_diff,
        "price_ratio": price_ratio,
        "lifespan_diff": lifespan_diff,

        "diameter_available": diameter_available,
        "diameter_diff": diameter_diff,
    }