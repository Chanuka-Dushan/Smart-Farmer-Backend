# backend/utils/vectorizer/vector_store.py

import os
import sys

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from models.research import PartVector


def upsert_part_vector(db, part_id: int, vector: list, vector_version: str = "tfidf_v1"):
    """
    Insert or update a part vector in the part_vectors table.
    """
    existing = db.query(PartVector).filter(PartVector.part_id == part_id).first()

    if existing:
        existing.vector = vector
        existing.vector_version = vector_version
    else:
        new_vector = PartVector(
            part_id=part_id,
            vector=vector,
            vector_version=vector_version
        )
        db.add(new_vector)

    db.commit()