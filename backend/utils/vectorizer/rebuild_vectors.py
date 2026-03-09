import os
import sys

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from utils.database import SessionLocal
from models.part import Part
from utils.vectorizer.vector_builder import build_vector
from utils.vectorizer.vector_store import upsert_part_vector


VECTOR_VERSION = "tfidf_v2"


def rebuild_all_part_vectors():
    db = SessionLocal()

    try:
        parts = db.query(Part).all()

        print("=" * 60)
        print("REBUILDING PART VECTORS")
        print(f"Total parts found: {len(parts)}")

        count = 0
        failed = 0

        for part in parts:
            try:
                vector = build_vector(part)

                upsert_part_vector(
                    db=db,
                    part_id=part.id,
                    vector=vector,
                    vector_version=VECTOR_VERSION
                )

                count += 1

                if count % 10 == 0:
                    print(f"{count} vectors stored/updated...")

            except Exception as e:
                failed += 1
                print(f"Failed for part_id={part.id}, name={part.name}: {e}")

        print("\nDONE")
        print(f"Stored/updated successfully: {count}")
        print(f"Failed: {failed}")
        print(f"Vector version used: {VECTOR_VERSION}")
        print("=" * 60)

    except Exception as e:
        print("Error while rebuilding vectors:", e)

    finally:
        db.close()


if __name__ == "__main__":
    rebuild_all_part_vectors()