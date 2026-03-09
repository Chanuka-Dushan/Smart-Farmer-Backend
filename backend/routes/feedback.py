from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db_session import SessionLocal
from models.part import Part
from models.research import FeedbackEvent
from models.schemas import FeedbackCreate   # ✅ correct import
from utils.feedback_service import get_feedback_score

router = APIRouter(
    tags=["Feedback"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/feedback")
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db)
):
    # Check query/original part exists
    query_part = db.query(Part).filter(Part.id == payload.part_id).first()
    if not query_part:
        raise HTTPException(status_code=404, detail="Query part not found")

    # Check recommended part exists
    recommended_part = db.query(Part).filter(Part.id == payload.recommended_part_id).first()
    if not recommended_part:
        raise HTTPException(status_code=404, detail="Recommended part not found")

    # Prevent same-part feedback
    if payload.part_id == payload.recommended_part_id:
        raise HTTPException(status_code=400, detail="part_id and recommended_part_id cannot be the same")

    feedback_event = FeedbackEvent(
        user_id=payload.user_id,
        part_id=payload.part_id,
        recommended_part_id=payload.recommended_part_id,
        feedback=payload.feedback
    )

    db.add(feedback_event)
    db.commit()
    db.refresh(feedback_event)

    return {
        "message": "Feedback saved successfully",
        "id": feedback_event.id,
        "user_id": feedback_event.user_id,
        "part_id": feedback_event.part_id,
        "recommended_part_id": feedback_event.recommended_part_id,
        "feedback": feedback_event.feedback,
        "timestamp": feedback_event.timestamp
    }

@router.get("/feedback-score")
def read_feedback_score(
    part_id: int,
    recommended_part_id: int,
    db: Session = Depends(get_db)
):
    score = get_feedback_score(db, part_id, recommended_part_id)

    return {
        "part_id": part_id,
        "recommended_part_id": recommended_part_id,
        "feedback_score": score
    }