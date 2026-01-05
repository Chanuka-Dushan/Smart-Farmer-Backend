from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.database import get_db
from models.part import Part
from utils.rule_recommender import calculate_rule_score
from utils.ml_similarity import calculate_ml_similarity


router = APIRouter(
    prefix="/recommend",
    tags=["Recommendation"]
)


# =========================================================
# Rule-Based Recommendation
# =========================================================
@router.get("/rule/{part_id}")
def recommend_rule_based(part_id: int, db: Session = Depends(get_db)):
    # 1️⃣ Get base part
    base_part = db.query(Part).filter(Part.id == part_id).first()

    if not base_part:
        raise HTTPException(status_code=404, detail="Base part not found")

    # 2️⃣ Get other parts
    all_parts = db.query(Part).filter(Part.id != part_id).all()

    recommendations = []

    # 3️⃣ Calculate rule-based score
    for part in all_parts:
        score, reasons = calculate_rule_score(base_part, part)

        if score > 0:
            recommendations.append({
                "part_id": part.id,
                "name": part.name,
                "brand": part.brand,
                "score": score,
                "reasons": reasons,
                "price": part.price,
                "lifespan": part.lifespan,
                "image_url": getattr(part, "image_url", None)
            })

    # 4️⃣ Sort by rule score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # 5️⃣ Response
    return {
        "base_part": {
            "id": base_part.id,
            "name": base_part.name,
            "brand": base_part.brand
        },
        "recommendations": recommendations
    }


# =========================================================
# Hybrid Recommendation (Rule-Based + ML Similarity)
# =========================================================
@router.get("/hybrid/{part_id}")
def recommend_hybrid(part_id: int, db: Session = Depends(get_db)):
    # 1️⃣ Get base part
    base_part = db.query(Part).filter(Part.id == part_id).first()

    if not base_part:
        raise HTTPException(status_code=404, detail="Base part not found")

    # 2️⃣ Get other parts
    all_parts = db.query(Part).filter(Part.id != part_id).all()

    results = []

    # 3️⃣ Calculate hybrid score
    for part in all_parts:
        rule_score, reasons = calculate_rule_score(base_part, part)
        ml_score = calculate_ml_similarity(base_part, part)

        final_score = round((rule_score * 0.6) + (ml_score * 0.4), 2)

        if final_score > 0:
            results.append({
                "part_id": part.id,
                "name": part.name,
                "brand": part.brand,
                "rule_score": rule_score,
                "ml_score": ml_score,
                "final_score": final_score,
                "reasons": reasons,
                "price": part.price,
                "lifespan": part.lifespan,
                "image_url": getattr(part, "image_url", None)
            })

    # 4️⃣ Sort by final hybrid score
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # 5️⃣ Response
    return {
        "base_part": {
            "id": base_part.id,
            "name": base_part.name,
            "brand": base_part.brand
        },
        "recommendations": results
    }

