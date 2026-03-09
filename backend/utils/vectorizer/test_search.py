import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from utils.vectorizer.search_service import search_parts


def run_search_test(query: str, top_k: int = 10):
    db = SessionLocal()
    try:
        result = search_parts(db=db, query=query, top_k=top_k)

        print("=" * 80)
        print("SEARCH TEST RESULT")
        print("Original Query   :", result["query"])
        print("Normalized Query :", result["normalized_query"])
        print("Total Results    :", result["total_results"])
        print("-" * 80)

        for item in result["results"]:
            print(f"Part ID            : {item['part_id']}")
            print(f"Name               : {item['name']}")
            print(f"Brand              : {item['brand']}")
            print(f"Machine Model      : {item['machine_model']}")
            print(f"Category           : {item['category']}")
            print(f"Compatibility      : {item['compatibility_group']}")
            print(f"Search Score       : {item['search_score']}")
            print(f"Semantic Score     : {item['semantic_score']}")
            print(f"Fuzzy Score        : {item['fuzzy_score']}")
            print(f"Token Overlap Score: {item['token_overlap_score']}")
            print(f"Model Hint Score   : {item['model_hint_score']}")
            print("-" * 80)

    except Exception as e:
        print("ERROR:", str(e))

    finally:
        db.close()


if __name__ == "__main__":
    test_queries = [
        "MF240 clutch plate 11 inch",
        "cluch fingr",
        "oil filtar",
        "pinon race",
        "tafe finger"
    ]

    for q in test_queries:
        run_search_test(query=q, top_k=5)