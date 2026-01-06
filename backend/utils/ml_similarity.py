import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def build_feature_vector(part):
    return np.array([
        part.diameter or 0,
        part.price or 0,
        part.lifespan or 0
    ], dtype=float)

def calculate_ml_similarity(base_part, candidate_part):
    v1 = build_feature_vector(base_part).reshape(1, -1)
    v2 = build_feature_vector(candidate_part).reshape(1, -1)

    similarity = cosine_similarity(v1, v2)[0][0]
    return round(similarity * 100, 2)  # scale to 0–100
