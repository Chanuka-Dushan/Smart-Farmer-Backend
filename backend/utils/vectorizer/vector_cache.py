# backend/utils/vectorizer/vector_cache.py

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


def _decode_vector(vector_payload: Any) -> Optional[List[float]]:
    if vector_payload is None:
        return None

    if isinstance(vector_payload, str):
        return json.loads(vector_payload)

    if isinstance(vector_payload, list):
        return vector_payload

    return _convert_vector_to_list(vector_payload)


def upsert_part_vector(
    db: Session,
    part_id: int,
    vector: Any,
    vector_version: str = "tfidf_v2"
) -> PartVector:
    vector_list = _convert_vector_to_list(vector)
    vector_payload = json.dumps(vector_list)

    existing = db.query(PartVector).filter(
        PartVector.part_id == part_id
    ).first()

    try:
        if existing:
            existing.vector = vector_payload
            existing.vector_version = vector_version
            saved_row = existing
        else:
            saved_row = PartVector(
                part_id=part_id,
                vector=vector_payload,
                vector_version=vector_version
            )
            db.add(saved_row)

        db.commit()
        db.refresh(saved_row)
        return saved_row

    except Exception:
        db.rollback()
        raise


def get_part_vector(db: Session, part_id: int) -> Optional[List[float]]:
    row = db.query(PartVector).filter(
        PartVector.part_id == part_id
    ).first()

    if not row:
        return None

    return _decode_vector(row.vector)


def get_vectors_by_part_ids(
    db: Session,
    part_ids: List[int]
) -> Dict[int, List[float]]:
    if not part_ids:
        return {}

    rows = db.query(PartVector).filter(
        PartVector.part_id.in_(part_ids)
    ).all()

    result: Dict[int, List[float]] = {}

    for row in rows:
        vector = _decode_vector(row.vector)
        if vector is not None:
            result[row.part_id] = vector

    return result


def rebuild_all_part_vectors(
    db: Session,
    vector_version: str = "tfidf_v2"
) -> dict:
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
            db.rollback()
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