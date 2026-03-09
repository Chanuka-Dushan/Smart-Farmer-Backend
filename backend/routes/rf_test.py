from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db_session import SessionLocal
from models.part import Part
from utils.ml.rf_predictor import predict_rf_probability

router = APIRouter(prefix="/ml", tags=["ML Test"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/rf-score")
def get_rf_score(part_id_1: int, part_id_2: int, db: Session = Depends(get_db)):
    part_a = db.query(Part).filter(Part.id == part_id_1).first()
    part_b = db.query(Part).filter(Part.id == part_id_2).first()

    if not part_a:
        raise HTTPException(status_code=404, detail=f"Part {part_id_1} not found")

    if not part_b:
        raise HTTPException(status_code=404, detail=f"Part {part_id_2} not found")

    try:
        rf_probability = predict_rf_probability(part_a, part_b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RF prediction failed: {str(e)}")

    prediction = "compatible" if rf_probability >= 0.5 else "incompatible"

    return {
        "part_id_1": part_id_1,
        "part_id_2": part_id_2,
        "part_1_name": part_a.name,
        "part_2_name": part_b.name,
        "rf_probability": round(rf_probability, 4),
        "prediction": prediction
    }