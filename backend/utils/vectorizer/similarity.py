# backend/utils/vectorizer/similarity.py

import os
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from utils.database import SessionLocal
from models.part import Part
from models.research import PartVector


def get_part_vector_map(db):
    """
    Load all stored vectors into a dictionary:
    {part_id: np.array(vector)}
    """
    rows = db.query(PartVector).all()
    vector_map = {}

    for row in rows:
        if row.vector:
            vector_map[row.part_id] = np.array(row.vector, dtype=float)

    return vector_map


def find_similar_parts(db, query_part_id: int, top_k: int = 5):
    """
    Find top-K similar parts based on stored vectors.
    """
    vector_map = get_part_vector_map(db)

    if query_part_id not in vector_map:
        raise ValueError(f"No vector found for part_id={query_part_id}")

    query_vector = vector_map[query_part_id].reshape(1, -1)

    results = []

    for part_id, candidate_vector in vector_map.items():
        if part_id == query_part_id:
            continue

        score = cosine_similarity(
            query_vector,
            candidate_vector.reshape(1, -1)
        )[0][0]

        part = db.query(Part).filter(Part.id == part_id).first()
        if part:
            results.append({
                "part_id": part.id,
                "name": part.name,
                "category": part.category,
                "machine_model": part.machine_model,
                "score": float(score)
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]


if __name__ == "__main__":
    db = SessionLocal()
    try:
        query_part_id = 1  # change this if needed

        query_part = db.query(Part).filter(Part.id == query_part_id).first()
        if not query_part:
            print(f"Part with ID {query_part_id} not found.")
        else:
            print("=" * 60)
            print("QUERY PART")
            print(f"ID: {query_part.id}")
            print(f"Name: {query_part.name}")
            print(f"Category: {query_part.category}")
            print(f"Machine Model: {query_part.machine_model}")
            print("=" * 60)

            similar_parts = find_similar_parts(db, query_part_id=query_part_id, top_k=5)

            print("\nTOP 5 SIMILAR PARTS")
            for idx, item in enumerate(similar_parts, start=1):
                print(
                    f"{idx}. ID={item['part_id']} | "
                    f"Name={item['name']} | "
                    f"Category={item['category']} | "
                    f"Model={item['machine_model']} | "
                    f"Score={item['score']:.4f}"
                )

    except Exception as e:
        print("Error while finding similar parts:", e)
    finally:
        db.close()