import os
import sys

print("START: test_vector_cache.py loaded")

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from models.part import Part
from utils.vectorizer.vector_builder import build_vector
from utils.vectorizer.vector_cache import (
    upsert_part_vector,
    get_part_vector,
    get_vectors_by_part_ids,
    rebuild_all_part_vectors,
)


def test_single_part():
    print("Running test_single_part()")
    db = SessionLocal()
    try:
        part = db.query(Part).first()

        if not part:
            print("No parts found in database.")
            return

        print("=" * 60)
        print("TEST SINGLE PART VECTOR CACHE")
        print(f"Part ID   : {part.id}")
        print(f"Part Name : {part.name}")

        vector = build_vector(part)

        saved = upsert_part_vector(
            db=db,
            part_id=part.id,
            vector=vector,
            vector_version="tfidf_v2"
        )

        print("Vector saved successfully.")
        print(f"Saved Row Part ID: {saved.part_id}")

        loaded_vector = get_part_vector(db, part.id)

        if loaded_vector is None:
            print("Loaded vector is None")
            return

        print(f"Loaded vector length: {len(loaded_vector)}")
        print(f"First 10 values: {loaded_vector[:10]}")
        print("=" * 60)

    except Exception as e:
        print("ERROR in test_single_part:", str(e))

    finally:
        db.close()


def test_multiple_vectors():
    print("Running test_multiple_vectors()")
    db = SessionLocal()
    try:
        parts = db.query(Part).limit(3).all()

        if not parts:
            print("No parts found in database for multi vector test.")
            return

        part_ids = [part.id for part in parts]
        vectors = get_vectors_by_part_ids(db, part_ids)

        print("=" * 60)
        print("TEST MULTIPLE VECTOR FETCH")
        print(f"Part IDs: {part_ids}")
        print(f"Fetched IDs: {list(vectors.keys())}")

        for pid, vec in vectors.items():
            print(f"Part ID {pid} -> vector length = {len(vec)}")

        print("=" * 60)

    except Exception as e:
        print("ERROR in test_multiple_vectors:", str(e))

    finally:
        db.close()


def test_rebuild_all():
    print("Running test_rebuild_all()")
    db = SessionLocal()
    try:
        result = rebuild_all_part_vectors(db, vector_version="tfidf_v2")

        print("=" * 60)
        print("REBUILD ALL RESULT")
        print(f"Message        : {result['message']}")
        print(f"Total Parts    : {result['total_parts']}")
        print(f"Success Count  : {result['success_count']}")
        print(f"Failure Count  : {result['failure_count']}")
        print(f"Vector Version : {result['vector_version']}")

        if result["failed_parts"]:
            print("Failed Parts:")
            for item in result["failed_parts"]:
                print(item)

        print("=" * 60)

    except Exception as e:
        print("ERROR in test_rebuild_all:", str(e))

    finally:
        db.close()


if __name__ == "__main__":
    print("ENTERED __main__")
    test_single_part()
    test_multiple_vectors()
    test_rebuild_all()
    print("END: script finished")