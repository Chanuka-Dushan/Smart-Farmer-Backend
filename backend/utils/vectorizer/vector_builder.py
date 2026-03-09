import os
import sys
import joblib
import pandas as pd

from scipy.sparse import hstack, csr_matrix

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from utils.vectorizer.text_builder import build_part_text
from utils.compatibility import get_model_group


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
ARTIFACTS_DIR = os.path.join(BACKEND_DIR, "models_artifacts")

TFIDF_PATH = os.path.join(ARTIFACTS_DIR, "tfidf.joblib")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.joblib")
ONEHOT_PATH = os.path.join(ARTIFACTS_DIR, "onehot.joblib")


# Global cache so artifacts are loaded only once
_tfidf = None
_scaler = None
_onehot = None


def _safe_number(value):
    """
    Convert numeric field safely to float.
    """
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value):
    """
    Convert value safely to lowercase string.
    """
    if value is None:
        return ""
    return str(value).strip().lower()


def load_artifacts():
    """
    Load saved vectorizer artifacts only once.
    """
    global _tfidf, _scaler, _onehot

    if _tfidf is None:
        _tfidf = joblib.load(TFIDF_PATH)

    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)

    if _onehot is None:
        _onehot = joblib.load(ONEHOT_PATH)

    return _tfidf, _scaler, _onehot


def build_vector(part):
    """
    Build final hybrid vector for one part using saved artifacts.
    Returns a fixed-length list.
    """
    tfidf, scaler, onehot = load_artifacts()

    # 1) text
    text = build_part_text(part)
    text_vec = tfidf.transform([text])

    # 2) numeric
    numeric = [[
        _safe_number(getattr(part, "price", 0)),
        _safe_number(getattr(part, "diameter", 0)),
        _safe_number(getattr(part, "lifespan", 0)),
    ]]
    num_vec_dense = scaler.transform(numeric)
    num_vec = csr_matrix(num_vec_dense)

    # 3) categorical
    machine_model = _safe_text(getattr(part, "machine_model", ""))
    category_df = pd.DataFrame([{
        "category": _safe_text(getattr(part, "category", "")),
        "machine_model": machine_model,
        "compatibility_group": get_model_group(machine_model),
    }])
    cat_vec = onehot.transform(category_df)

    # 4) combine all
    final_vec = hstack([text_vec, cat_vec, num_vec])

    # Return as normal Python list
    return final_vec.toarray()[0].tolist()


if __name__ == "__main__":
    from utils.database import SessionLocal
    from models.part import Part

    db = SessionLocal()
    try:
        part = db.query(Part).first()

        if not part:
            print("No parts found in database.")
        else:
            vector = build_vector(part)
            print("Part ID:", part.id)
            print("Part Name:", part.name)
            print("Machine Model:", getattr(part, "machine_model", None))
            print("Compatibility Group:", get_model_group(getattr(part, "machine_model", "")))
            print("Vector length:", len(vector))
            print("First 10 values:", vector[:10])

    except Exception as e:
        print("Error while building vector:", e)

    finally:
        db.close()