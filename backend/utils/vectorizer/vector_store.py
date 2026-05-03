# backend/utils/vectorizer/vector_store.py

import os
import sys
import json

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.part_vector import PartVector


def upsert_part_vector(db, part_id: int, vector: list, vector_version: str = "tfidf_v2"):
    """
    Insert or update a part vector in the part_vectors table.

    SQLite cannot store Python lists directly, so vector is saved as JSON string.
    """
    try:
        vector_json = json.dumps(vector)

        existing = db.query(PartVector).filter(
            PartVector.part_id == part_id
        ).first()

        if existing:
            existing.vector = vector_json
            existing.vector_version = vector_version
        else:
            new_vector = PartVector(
                part_id=part_id,
                vector=vector_json,
                vector_version=vector_version
            )
            db.add(new_vector)

        db.commit()

    except Exception:
        db.rollback()
        raise