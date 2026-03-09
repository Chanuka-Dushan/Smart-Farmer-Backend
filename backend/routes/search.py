from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db_session import SessionLocal
from utils.vectorizer.search_service import search_parts

router = APIRouter(tags=["Search"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def search_endpoint(
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    try:
        return search_parts(db=db, query=q, top_k=top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))