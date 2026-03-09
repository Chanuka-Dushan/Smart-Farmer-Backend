from sqlalchemy import func, case
from sqlalchemy.orm import Session

from models.research import FeedbackEvent


def get_feedback_score(db: Session, part_id: int, recommended_part_id: int) -> float:
    result = db.query(
        func.count(FeedbackEvent.id).label("total"),
        func.sum(
            case(
                (FeedbackEvent.feedback == "accept", 1),
                else_=0
            )
        ).label("accept_count"),
        func.sum(
            case(
                (FeedbackEvent.feedback == "reject", 1),
                else_=0
            )
        ).label("reject_count")
    ).filter(
        FeedbackEvent.part_id == part_id,
        FeedbackEvent.recommended_part_id == recommended_part_id
    ).first()

    total = result.total or 0
    accept_count = result.accept_count or 0
    reject_count = result.reject_count or 0

    raw_score = (accept_count - reject_count) / (total + 1)
    normalized_score = (raw_score + 1) / 2

    return round(normalized_score, 4)