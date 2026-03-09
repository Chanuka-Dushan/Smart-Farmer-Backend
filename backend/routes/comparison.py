from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db_session import SessionLocal
from utils.vectorizer.comparison_service import compare_parts as compare_parts_service

router = APIRouter(tags=["Comparison"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/compare")
def compare_parts_endpoint(
    original_part_id: int = Query(...),
    alternative_part_id: int = Query(...),
    db: Session = Depends(get_db)
):
    try:
        return compare_parts_service(
            db=db,
            original_part_id=original_part_id,
            alternative_part_id=alternative_part_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))