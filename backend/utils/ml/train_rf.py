import os
import sys
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from models.part import Part
from utils.ml.pair_features import build_pair_features


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CSV_PATH = os.path.join(BASE_DIR, "data", "compatibility_pairs.csv")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "models_artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "random_forest.joblib")
FEATURES_PATH = os.path.join(ARTIFACTS_DIR, "rf_feature_columns.joblib")


def main():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    db = SessionLocal()

    X_rows = []
    y = []

    try:
        for _, row in df.iterrows():
            p1 = db.query(Part).filter(Part.id == int(row["part_id_1"])).first()
            p2 = db.query(Part).filter(Part.id == int(row["part_id_2"])).first()

            if not p1 or not p2:
                continue

            feats = build_pair_features(p1, p2)
            X_rows.append(feats)
            y.append(int(row["label"]))
    finally:
        db.close()

    X = pd.DataFrame(X_rows)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("Accuracy:", accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(list(X.columns), FEATURES_PATH)

    print("Model saved:", MODEL_PATH)


if __name__ == "__main__":
    main()