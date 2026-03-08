from typing import List, Dict, Any, Tuple
import sys
import os

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.part import Part
from utils.vectorizer.text_builder import build_part_text
from utils.database import SessionLocal
from utils.compatibility import get_model_group


def _safe_number(value: Any) -> float:
    """
    Convert numeric field safely to float.
    If None or invalid, return 0.0
    """
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value: Any) -> str:
    """
    Convert value safely to string.
    If None -> empty string.
    """
    if value is None:
        return ""
    return str(value).strip()


def get_all_parts(db) -> List[Part]:
    """
    Fetch all parts from database.
    """
    return db.query(Part).all()


def build_dataset(db) -> Tuple[List[int], List[str], List[List[float]], List[Dict[str, str]]]:
    """
    Build aligned training dataset from all parts.

    Returns:
        part_ids: [1, 2, 3, ...]
        texts: ["oil filter ...", "bearing ..."]
        numeric: [[price, diameter, lifespan], ...]
        categories: [
            {
                "category": "...",
                "machine_model": "...",
                "compatibility_group": "..."
            },
            ...
        ]
    """
    parts = get_all_parts(db)

    part_ids = []
    texts = []
    numeric = []
    categories = []

    for part in parts:
        # part id
        part_ids.append(part.id)

        # text features
        text = build_part_text(part)
        texts.append(text)

        # numeric features
        numeric_row = [
            _safe_number(getattr(part, "price", 0)),
            _safe_number(getattr(part, "diameter", 0)),
            _safe_number(getattr(part, "lifespan", 0)),
        ]
        numeric.append(numeric_row)

        # categorical features
        machine_model = _safe_text(getattr(part, "machine_model", ""))
        category_row = {
            "category": _safe_text(getattr(part, "category", "")),
            "machine_model": machine_model,
            "compatibility_group": get_model_group(machine_model),
        }
        categories.append(category_row)

    return part_ids, texts, numeric, categories


if __name__ == "__main__":
    db = SessionLocal()
    try:
        part_ids, texts, numeric, categories = build_dataset(db)

        print("Total parts:", len(part_ids))
        print("First 3 part_ids:", part_ids[:3])
        print("First 2 texts:", texts[:2])
        print("First 2 numeric rows:", numeric[:2])
        print("First 2 categories:", categories[:2])

    except Exception as e:
        print("Error while building dataset:", e)

    finally:
        db.close()