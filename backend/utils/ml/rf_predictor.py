import os
import sys
import joblib
import pandas as pd

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from utils.ml.pair_features import build_pair_features

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "models_artifacts")

MODEL_PATH = os.path.join(ARTIFACTS_DIR, "random_forest.joblib")
FEATURES_PATH = os.path.join(ARTIFACTS_DIR, "rf_feature_columns.joblib")

_rf_model = None
_rf_columns = None


def load_rf_model():
    global _rf_model, _rf_columns

    if _rf_model is None:
        _rf_model = joblib.load(MODEL_PATH)

    if _rf_columns is None:
        _rf_columns = joblib.load(FEATURES_PATH)

    return _rf_model, _rf_columns


def predict_rf_probability(part_a, part_b) -> float:
    model, feature_columns = load_rf_model()

    feature_dict = build_pair_features(part_a, part_b)
    df = pd.DataFrame([feature_dict])

    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0.0

    df = df[feature_columns]

    prob = model.predict_proba(df)[0][1]
    return float(prob)