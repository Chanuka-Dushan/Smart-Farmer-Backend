import os
import sys
import json
from typing import Any, Dict, List, Optional

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from sqlalchemy.orm import Session

from models.part import Part
from models.part_vector import PartVector
from utils.vectorizer.vector_builder import build_vector


def _convert_vector_to_list(vector: Any) -> List[float]:
    """
    Convert sparse/numpy/list vector into a normal Python list.
    """
    if vector is None:
        return []

    if hasattr(vector, "toarray"):
        dense = vector.toarray()
        if len(dense.shape) == 2:
            return dense[0].tolist()
        return dense.tolist()

    if hasattr(vector, "tolist"):
        data = vector.tolist()
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            return data[0]
        return data

    if isinstance(vector, list):
        return vector

    raise ValueError("Unsupported vector format")


def upsert_part_vector(
    db: Session,
    part_id: int,
    vector: Any,
    vector_version: str = "v1"
) -> PartVector:
    """
    Insert or update cached vector for a part.
    """
    vector_list = _convert_vector_to_list(vector)
    vector_payload = json.dumps(vector_list)

    existing = db.query(PartVector).filter(PartVector.part_id == part_id).first()

    if existing:
        existing.vector = vector_payload
        existing.vector_version = vector_version
        db.commit()
        db.refresh(existing)
        return existing

    new_row = PartVector(
        part_id=part_id,
        vector=vector_payload,
        vector_version=vector_version
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row


def get_part_vector(db: Session, part_id: int) -> Optional[List[float]]:
    """
    Get cached vector for one part as Python list.
    """
    row = db.query(PartVector).filter(PartVector.part_id == part_id).first()

    if not row or row.vector is None:
        return None

    if isinstance(row.vector, str):
        return json.loads(row.vector)

    if isinstance(row.vector, list):
        return row.vector

    return row.vector


def get_vectors_by_part_ids(db: Session, part_ids: List[int]) -> Dict[int, List[float]]:
    """
    Get cached vectors for multiple part IDs.
    Returns:
    {
        1: [...],
        2: [...]
    }
    """
    if not part_ids:
        return {}

    rows = db.query(PartVector).filter(PartVector.part_id.in_(part_ids)).all()

    result: Dict[int, List[float]] = {}

    for row in rows:
        if row.vector is None:
            continue

        if isinstance(row.vector, str):
            result[row.part_id] = json.loads(row.vector)
        elif isinstance(row.vector, list):
            result[row.part_id] = row.vector
        else:
            result[row.part_id] = row.vector

    return result


def rebuild_all_part_vectors(db: Session, vector_version: str = "v1") -> dict:
    """
    Build and cache vectors for all parts.
    """
    parts = db.query(Part).all()

    total_parts = len(parts)
    success_count = 0
    failure_count = 0
    failed_parts = []

    for part in parts:
        try:
            vec = build_vector(part)

            upsert_part_vector(
                db=db,
                part_id=part.id,
                vector=vec,
                vector_version=vector_version
            )

            success_count += 1

        except Exception as e:
            failure_count += 1
            failed_parts.append({
                "part_id": part.id,
                "name": getattr(part, "name", None),
                "error": str(e)
            })

    return {
        "message": "Vector rebuild completed",
        "total_parts": total_parts,
        "success_count": success_count,
        "failure_count": failure_count,
        "vector_version": vector_version,
        "failed_parts": failed_parts
    }