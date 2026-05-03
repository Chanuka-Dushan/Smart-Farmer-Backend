import os
import sys
import random
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from models.part import Part
from utils.ml.pair_features import build_pair_features


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "models_artifacts")

MODEL_PATH = os.path.join(ARTIFACTS_DIR, "random_forest.joblib")
FEATURES_PATH = os.path.join(ARTIFACTS_DIR, "rf_feature_columns.joblib")
IMPORTANCE_PATH = os.path.join(ARTIFACTS_DIR, "rf_feature_importance.csv")

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def generate_training_pairs(parts):
    pairs = []

    # Positive pairs: same compatibility group
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            p1 = parts[i]
            p2 = parts[j]

            if (
                p1.compatibility_group
                and p2.compatibility_group
                and p1.compatibility_group == p2.compatibility_group
            ):
                pairs.append((p1.id, p2.id, 1))

    # Hard negative pairs: similar but not compatible
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            p1 = parts[i]
            p2 = parts[j]

            same_category = p1.category == p2.category
            same_family = p1.machine_family == p2.machine_family
            same_function = p1.function_type == p2.function_type
            different_group = p1.compatibility_group != p2.compatibility_group

            if different_group and (same_category or same_family or same_function):
                pairs.append((p1.id, p2.id, 0))

    return pairs


def balance_pairs(pairs):
    positives = [p for p in pairs if p[2] == 1]
    negatives = [p for p in pairs if p[2] == 0]

    min_count = min(len(positives), len(negatives))

    if min_count == 0:
        raise ValueError("Need both positive and negative pairs for training.")

    positives = random.sample(positives, min_count)
    negatives = random.sample(negatives, min_count)

    balanced = positives + negatives
    random.shuffle(balanced)

    return balanced


def apply_label_noise(pairs, noise_rate=0.07):
    noisy_pairs = []

    for part_id_1, part_id_2, label in pairs:
        if random.random() < noise_rate:
            label = 1 - label

        noisy_pairs.append((part_id_1, part_id_2, label))

    return noisy_pairs


def main():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    db = SessionLocal()

    X_rows = []
    y = []

    try:
        parts = db.query(Part).all()

        print("=" * 60)
        print("PARTS LOADED:", len(parts))

        pairs = generate_training_pairs(parts)
        print("Generated pairs before balancing:", len(pairs))

        pairs = balance_pairs(pairs)
        print("Balanced pairs:", len(pairs))

        pairs = apply_label_noise(pairs, noise_rate=0.07)
        print("Applied label noise: 7%")

        for part_id_1, part_id_2, label in pairs:
            p1 = db.query(Part).filter(Part.id == part_id_1).first()
            p2 = db.query(Part).filter(Part.id == part_id_2).first()

            if not p1 or not p2:
                continue

            features = build_pair_features(db, p1, p2)

            X_rows.append(features)
            y.append(label)

    finally:
        db.close()

    if len(X_rows) == 0:
        raise ValueError("No training data generated.")

    X = pd.DataFrame(X_rows)
    y_series = pd.Series(y)

    print("=" * 60)
    print("RANDOM FOREST TRAINING DATA")
    print("Total training pairs:", len(X))
    print("Feature columns:", list(X.columns))
    print("Label distribution:")
    print(y_series.value_counts())
    print("=" * 60)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=80,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=3,
        random_state=RANDOM_SEED,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    cv_scores = cross_val_score(model, X, y, cv=5)

    print("\nCROSS VALIDATION")
    print("CV scores:", cv_scores)
    print("Mean CV score:", round(cv_scores.mean(), 4))

    preds = model.predict(X_test)

    print("\nMODEL EVALUATION")
    print("Accuracy:", accuracy_score(y_test, preds))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, preds))

    print("\nClassification Report:")
    print(classification_report(y_test, preds, zero_division=0))

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    }).sort_values(by="importance", ascending=False)

    print("\nFEATURE IMPORTANCE")
    print(importance_df)

    importance_df.to_csv(IMPORTANCE_PATH, index=False)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(list(X.columns), FEATURES_PATH)

    print("\nMODEL SAVED")
    print("Model:", MODEL_PATH)
    print("Features:", FEATURES_PATH)
    print("Feature importance:", IMPORTANCE_PATH)


if __name__ == "__main__":
    main()