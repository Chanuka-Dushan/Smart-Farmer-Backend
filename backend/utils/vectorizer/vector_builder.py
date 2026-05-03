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


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
ARTIFACTS_DIR = os.path.join(BACKEND_DIR, "models_artifacts")

TFIDF_PATH = os.path.join(ARTIFACTS_DIR, "tfidf.joblib")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.joblib")
ONEHOT_PATH = os.path.join(ARTIFACTS_DIR, "onehot.joblib")


_tfidf = None
_scaler = None
_onehot = None


CATEGORY_COLUMNS = [
    "category",
    "machine_model",
    "machine_family",
    "function_type",
    "compatibility_group",
]


def _safe_number(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def load_artifacts():
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
    Build final vector for one part using saved TF-IDF, scaler, and OneHotEncoder.
    Must use same categorical columns as train_vectorizer.py.
    """
    tfidf, scaler, onehot = load_artifacts()

    # 1) Text vector
    text = build_part_text(part)
    text_vec = tfidf.transform([text])

    # 2) Numeric vector
    numeric = [[
        _safe_number(getattr(part, "price", 0)),
        _safe_number(getattr(part, "diameter", 0)),
        _safe_number(getattr(part, "lifespan", 0)),
    ]]

    num_vec_dense = scaler.transform(numeric)
    num_vec = csr_matrix(num_vec_dense)

    # 3) Categorical vector
    category_row = {
        "category": _safe_text(getattr(part, "category", "")),
        "machine_model": _safe_text(getattr(part, "machine_model", "")),
        "machine_family": _safe_text(getattr(part, "machine_family", "")),
        "function_type": _safe_text(getattr(part, "function_type", "")),
        "compatibility_group": _safe_text(getattr(part, "compatibility_group", "")),
    }

    category_df = pd.DataFrame([category_row])

    # Force same column order as training
    category_df = category_df[CATEGORY_COLUMNS]

    cat_vec = onehot.transform(category_df)

    # 4) Combine all vectors
    final_vec = hstack([text_vec, cat_vec, num_vec])

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
            print("Category:", getattr(part, "category", None))
            print("Machine Model:", getattr(part, "machine_model", None))
            print("Machine Family:", getattr(part, "machine_family", None))
            print("Function Type:", getattr(part, "function_type", None))
            print("Compatibility Group:", getattr(part, "compatibility_group", None))
            print("Vector length:", len(vector))
            print("First 10 values:", vector[:10])

    except Exception as e:
        print("Error while building vector:", e)

    finally:
        db.close()