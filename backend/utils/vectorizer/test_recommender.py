import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from utils.vectorizer.recommender import recommend_parts


def run_test(part_id: int, top_k: int = 5):
    db = SessionLocal()
    try:
        result = recommend_parts(db=db, part_id=part_id, top_k=top_k)

        print("=" * 80)
        print(f"RECOMMENDER TEST RESULT FOR PART ID {part_id}")
        print("Query Part:", result["query_part"])
        print("Total Candidates:", result["total_candidates"])
        print("-" * 80)

        if not result["recommendations"]:
            print("No recommendations found.")
            print("-" * 80)
            return

        for item in result["recommendations"]:
            print(f"Recommended Part ID : {item['recommended_part']}")
            print(f"Name                : {item['name']}")
            print(f"Category            : {item['category']}")
            print(f"Machine Model       : {item['machine_model']}")
            print(f"Compatibility Group : {item['compatibility_group']}")
            print(f"Hybrid Score        : {item['hybrid_score']}")
            print(f"Feedback Score      : {item['feedback_score']}")
            print(f"Final Score         : {item['final_score']}")
            print(f"Similarity %        : {item['similarity_percentage']}")
            print(f"Explanation         : {item['explanation']}")
            print("-" * 80)

    except Exception as e:
        print(f"ERROR for part {part_id}: {str(e)}")

    finally:
        db.close()


if __name__ == "__main__":
    # Change these IDs based on the parts you want to test
    test_ids = [34, 57, 70]

    for pid in test_ids:
        run_test(part_id=pid, top_k=5)