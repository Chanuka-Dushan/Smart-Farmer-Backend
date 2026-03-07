# backend/utils/vectorizer/train_vectorizer.py

import os
import sys
import joblib
import pandas as pd

from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from utils.vectorizer.dataset import build_dataset
from utils.database import SessionLocal


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
ARTIFACTS_DIR = os.path.join(BACKEND_DIR, "models_artifacts")

TFIDF_PATH = os.path.join(ARTIFACTS_DIR, "tfidf.joblib")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.joblib")
ONEHOT_PATH = os.path.join(ARTIFACTS_DIR, "onehot.joblib")


def ensure_artifacts_dir():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def train_vector_pipeline():
    db = SessionLocal()

    try:
        part_ids, texts, numeric, categories = build_dataset(db)

        print("=" * 60)
        print("DATASET LOADED")
        print(f"Total parts: {len(part_ids)}")

        if len(part_ids) == 0:
            raise ValueError("No parts found in database. Cannot train vectorizer.")

        # categories -> DataFrame
        categories_df = pd.DataFrame(categories)

        # 1) TF-IDF
        tfidf = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            stop_words="english"
        )
        text_vec = tfidf.fit_transform(texts)

        print("\nTF-IDF trained successfully")
        print("Text vector shape:", text_vec.shape)

        # 2) Numeric scaler
        scaler = StandardScaler()
        num_vec = scaler.fit_transform(numeric)

        print("\nNumeric scaler trained successfully")
        print("Numeric vector shape:", num_vec.shape)

        # 3) One-hot encoder
        try:
            onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
        except TypeError:
            onehot = OneHotEncoder(handle_unknown="ignore", sparse=True)

        cat_vec = onehot.fit_transform(categories_df)

        print("\nOneHot encoder trained successfully")
        print("Category vector shape:", cat_vec.shape)

        # 4) Combine all vectors
        final_matrix = hstack([text_vec, cat_vec, num_vec])

        print("\nFINAL VECTOR MATRIX CREATED")
        print("Final matrix shape:", final_matrix.shape)

        # 5) Save artifacts
        ensure_artifacts_dir()

        joblib.dump(tfidf, TFIDF_PATH)
        joblib.dump(scaler, SCALER_PATH)
        joblib.dump(onehot, ONEHOT_PATH)

        print("\nARTIFACTS SAVED")
        print("TF-IDF saved to:", TFIDF_PATH)
        print("Scaler saved to:", SCALER_PATH)
        print("OneHot saved to:", ONEHOT_PATH)

        print("=" * 60)

        return {
            "total_parts": len(part_ids),
            "text_shape": text_vec.shape,
            "numeric_shape": num_vec.shape,
            "category_shape": cat_vec.shape,
            "final_shape": final_matrix.shape,
        }

    finally:
        db.close()


if __name__ == "__main__":
    try:
        result = train_vector_pipeline()
        print("\nTRAINING SUMMARY")
        print(result)
    except Exception as e:
        print("Error while training vector pipeline:", e)