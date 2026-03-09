import os
import sys
from typing import Dict

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from sklearn.metrics.pairwise import cosine_similarity
from models.part import Part
from utils.vectorizer.vector_cache import get_part_vector


def safe_float(v):
    try:
        if v is None:
            return 0.0
        return float(v)
    except:
        return 0.0


def safe_str(v):
    if v is None:
        return ""
    return str(v).strip().lower()


def get_similarity_score(part_a: Part, part_b: Part) -> float:
    try:
        vec_a = get_part_vector(part_a.id)
        vec_b = get_part_vector(part_b.id)

        if vec_a is None or vec_b is None:
            return 0.0

        return float(cosine_similarity(vec_a, vec_b)[0][0])
    except:
        return 0.0


def build_pair_features(part_a: Part, part_b: Part) -> Dict[str, float]:
    sim = get_similarity_score(part_a, part_b)

    return {
        "same_category": int(safe_str(part_a.category) == safe_str(part_b.category)),
        "same_machine_model": int(safe_str(getattr(part_a, "machine_model", "")) == safe_str(getattr(part_b, "machine_model", ""))),
        "same_compatibility_group": int(safe_str(getattr(part_a, "compatibility_group", "")) == safe_str(getattr(part_b, "compatibility_group", ""))),
        "same_brand": int(safe_str(part_a.brand) == safe_str(part_b.brand)),
        "same_material": int(safe_str(getattr(part_a, "material", "")) == safe_str(getattr(part_b, "material", ""))),
        "price_diff": abs(safe_float(part_a.price) - safe_float(part_b.price)),
        "diameter_diff": abs(safe_float(getattr(part_a, "diameter", 0)) - safe_float(getattr(part_b, "diameter", 0))),
        "lifespan_diff": abs(safe_float(getattr(part_a, "lifespan", 0)) - safe_float(getattr(part_b, "lifespan", 0))),
        "similarity_score": sim,
    }