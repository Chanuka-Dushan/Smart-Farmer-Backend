from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db_session import SessionLocal
from utils.vectorizer.recommender import recommend_parts

router = APIRouter(
    tags=["Recommender"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/recommend/{part_id}")
def get_recommendations(
    part_id: int,
    top_k: int = Query(5, ge=1, le=20),
    mode: str = Query("normal", pattern="^(normal|before_after)$"),
    db: Session = Depends(get_db)
):
    try:
        return recommend_parts(
            db=db,
            part_id=part_id,
            top_k=top_k,
            mode=mode
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))