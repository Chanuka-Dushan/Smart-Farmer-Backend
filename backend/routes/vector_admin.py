from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db_session import SessionLocal
from utils.vectorizer.vector_cache import rebuild_all_part_vectors

router = APIRouter(
    prefix="/admin",
    tags=["Vector Admin"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/rebuild-vectors")
def rebuild_vectors(db: Session = Depends(get_db)):
    """
    Rebuild and cache vectors for all parts.
    """
    result = rebuild_all_part_vectors(db, vector_version="tfidf_v2")
    return result