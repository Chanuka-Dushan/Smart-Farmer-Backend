import os
import sys
import random
from typing import Dict, List, Tuple

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from db_session import SessionLocal
from models.part import Part
from utils.feedback_service import get_feedback_score
from utils.ml.pair_features import build_pair_features, get_similarity_score
from utils.ml.rf_predictor import predict_rf_probability


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "models_artifacts")

RECOMMENDER_RESULTS_PATH = os.path.join(
    ARTIFACTS_DIR, "recommender_evaluation.csv"
)

RF_METRICS_PATH = os.path.join(
    ARTIFACTS_DIR, "rf_classifier_metrics.csv"
)

RF_MODEL_PATH = os.path.join(
    ARTIFACTS_DIR, "random_forest.joblib"
)

RF_FEATURES_PATH = os.path.join(
    ARTIFACTS_DIR, "rf_feature_columns.joblib"
)

RANDOM_SEED = 42
TOP_K = 5


def safe_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def hard_rule_pass(query_part: Part, candidate: Part) -> bool:
    """
    Same hard rules used in Phase 3.
    These are filtering rules, not final scoring features.
    """
    return (
        query_part.id != candidate.id
        and safe_str(query_part.category) == safe_str(candidate.category)
        and safe_str(query_part.machine_family) == safe_str(candidate.machine_family)
        and safe_str(query_part.compatibility_group) == safe_str(candidate.compatibility_group)
        and safe_str(query_part.function_type) == safe_str(candidate.function_type)
    )


def is_relevant(query_part: Part, candidate: Part) -> bool:
    """
    Ground-truth relevance for evaluation.

    Since we have limited labelled real-world compatibility data,
    compatibility_group is used as weak ground truth.
    """
    return (
        query_part.id != candidate.id
        and safe_str(query_part.compatibility_group) != ""
        and safe_str(query_part.compatibility_group) == safe_str(candidate.compatibility_group)
    )


def calculate_variant_score(
    db,
    query_part: Part,
    candidate: Part,
    variant: str
) -> float:

    sim = get_similarity_score(db, query_part, candidate)
    feedback = get_feedback_score(db, query_part.id, candidate.id)
    ml = predict_rf_probability(db=db, part_a=query_part, part_b=candidate)

    rules_passed = hard_rule_pass(query_part, candidate)

    if variant == "rules_only":
        return 1.0 if rules_passed else 0.0

    if variant == "similarity_only":
        return sim

    if variant == "similarity_feedback":
        return 0.80 * sim + 0.20 * feedback

    if variant == "rf_assisted":
        return 0.70 * sim + 0.30 * ml

    if variant == "hybrid_final":
        if not rules_passed:
            return -1.0

        return 0.50 * sim + 0.30 * ml + 0.20 * feedback

    return 0.0


def precision_at_k(top_candidates: List[Part], relevant_ids: set, k: int) -> float:
    if k == 0:
        return 0.0

    top_k = top_candidates[:k]
    hits = sum(1 for part in top_k if part.id in relevant_ids)

    return hits / k


def recall_at_k(top_candidates: List[Part], relevant_ids: set, k: int) -> float:
    if not relevant_ids:
        return 0.0

    top_k = top_candidates[:k]
    hits = sum(1 for part in top_k if part.id in relevant_ids)

    return hits / len(relevant_ids)


def evaluate_recommender_variants(db) -> pd.DataFrame:
    variants = [
        "rules_only",
        "similarity_only",
        "similarity_feedback",
        "rf_assisted",
        "hybrid_final"
    ]

    parts = db.query(Part).all()

    results = []

    for variant in variants:
        precision_scores = []
        recall_scores = []

        for query_part in parts:
            candidates = [p for p in parts if p.id != query_part.id]

            relevant_ids = {
                c.id for c in candidates
                if is_relevant(query_part, c)
            }

            if not relevant_ids:
                continue

            scored_candidates = []

            for candidate in candidates:
                score = calculate_variant_score(
                    db=db,
                    query_part=query_part,
                    candidate=candidate,
                    variant=variant
                )

                scored_candidates.append((candidate, score))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            ranked_candidates = [item[0] for item in scored_candidates]

            precision_scores.append(
                precision_at_k(ranked_candidates, relevant_ids, TOP_K)
            )

            recall_scores.append(
                recall_at_k(ranked_candidates, relevant_ids, TOP_K)
            )

        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
        avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0

        results.append({
            "variant": variant,
            f"precision@{TOP_K}": round(avg_precision, 4),
            f"recall@{TOP_K}": round(avg_recall, 4),
            "evaluated_queries": len(precision_scores)
        })

    return pd.DataFrame(results)


def generate_training_pairs(parts: List[Part]) -> List[Tuple[int, int, int]]:
    pairs = []

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


def balance_pairs(pairs: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
    positives = [p for p in pairs if p[2] == 1]
    negatives = [p for p in pairs if p[2] == 0]

    min_count = min(len(positives), len(negatives))

    if min_count == 0:
        raise ValueError("Need both positive and negative pairs for RF evaluation.")

    positives = random.sample(positives, min_count)
    negatives = random.sample(negatives, min_count)

    balanced = positives + negatives
    random.shuffle(balanced)

    return balanced


def apply_label_noise(
    pairs: List[Tuple[int, int, int]],
    noise_rate: float = 0.07
) -> List[Tuple[int, int, int]]:

    noisy_pairs = []

    for part_id_1, part_id_2, label in pairs:
        if random.random() < noise_rate:
            label = 1 - label

        noisy_pairs.append((part_id_1, part_id_2, label))

    return noisy_pairs


def evaluate_rf_classifier(db) -> pd.DataFrame:
    random.seed(RANDOM_SEED)

    model = joblib.load(RF_MODEL_PATH)
    feature_columns = joblib.load(RF_FEATURES_PATH)

    parts = db.query(Part).all()
    parts_by_id = {p.id: p for p in parts}

    pairs = generate_training_pairs(parts)
    pairs = balance_pairs(pairs)
    pairs = apply_label_noise(pairs, noise_rate=0.07)

    X_rows = []
    y = []

    for part_id_1, part_id_2, label in pairs:
        p1 = parts_by_id.get(part_id_1)
        p2 = parts_by_id.get(part_id_2)

        if not p1 or not p2:
            continue

        features = build_pair_features(db, p1, p2)
        X_rows.append(features)
        y.append(label)

    X = pd.DataFrame(X_rows)

    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0.0

    X = X[feature_columns]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=y
    )

    predictions = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1_score": f1_score(y_test, predictions, zero_division=0),
    }

    return pd.DataFrame([
        {
            "metric": metric,
            "value": round(value, 4)
        }
        for metric, value in metrics.items()
    ])


def main():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    db = SessionLocal()

    try:
        print("=" * 60)
        print("PHASE 5: RECOMMENDER EVALUATION")
        print("=" * 60)

        recommender_df = evaluate_recommender_variants(db)
        recommender_df.to_csv(RECOMMENDER_RESULTS_PATH, index=False)

        print("\nTABLE 1 — RECOMMENDER PERFORMANCE")
        print(recommender_df)

        print("\nSaved:", RECOMMENDER_RESULTS_PATH)

        print("\n" + "=" * 60)
        print("PHASE 5: RF CLASSIFIER EVALUATION")
        print("=" * 60)

        rf_df = evaluate_rf_classifier(db)
        rf_df.to_csv(RF_METRICS_PATH, index=False)

        print("\nTABLE 2 — RF CLASSIFIER PERFORMANCE")
        print(rf_df)

        print("\nSaved:", RF_METRICS_PATH)

        best_row = recommender_df.sort_values(
            by=f"precision@{TOP_K}",
            ascending=False
        ).iloc[0]

        print("\nBEST RECOMMENDER VARIANT")
        print(
            f"{best_row['variant']} "
            f"with Precision@{TOP_K} = {best_row[f'precision@{TOP_K}']}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()