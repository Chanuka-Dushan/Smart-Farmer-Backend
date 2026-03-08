import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from utils.vectorizer.comparison_service import compare_parts


def run_test(original_part_id: int, alternative_part_id: int):
    db = SessionLocal()
    try:
        result = compare_parts(
            db=db,
            original_part_id=original_part_id,
            alternative_part_id=alternative_part_id
        )

        print("=" * 80)
        print("COMPARISON TEST RESULT")
        print("Original Part:", result["original_part"]["name"], "|", result["original_part"]["machine_model"])
        print("Alternative Part:", result["alternative_part"]["name"], "|", result["alternative_part"]["machine_model"])
        print("-" * 80)

        print("Comparison Summary:")
        for key, value in result["comparison"].items():
            print(f"{key}: {value}")

        print("-" * 80)
        print("Compatibility Reason:", result["compatibility_reason"])

        print("-" * 80)
        print("Recommendation Scores:")
        for key, value in result["recommendation_scores"].items():
            print(f"{key}: {value}")

        print("-" * 80)
        print("Explanation:")
        for item in result["explanation"]:
            print("-", item)

        print("=" * 80)

    except Exception as e:
        print("ERROR:", str(e))

    finally:
        db.close()


if __name__ == "__main__":
    # Example:
    # original = TAFE 7250 Clutch Finger
    # alternative = MF 240 Clutch Finger
    run_test(original_part_id=34, alternative_part_id=70)