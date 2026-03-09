# backend/routes/similarity.py

import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Add backend folder to Python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
)

from utils.database import get_db
from utils.vectorizer.similarity import find_similar_parts
from models.part import Part

router = APIRouter(prefix="/parts", tags=["Part Similarity"])


@router.get("/{part_id}/similar")
def get_similar_parts(part_id: int, top_k: int = 5, db: Session = Depends(get_db)):
    """
    Return top-K similar parts for a given part ID.
    This is a semantic similarity endpoint, not the final filtered recommender.
    """
    query_part = db.query(Part).filter(Part.id == part_id).first()
    if not query_part:
        raise HTTPException(status_code=404, detail="Part not found")

    try:
        results = find_similar_parts(db, query_part_id=part_id, top_k=top_k)
        return {
            "query_part_id": query_part.id,
            "query_part_name": query_part.name,
            "top_k": top_k,
            "similar_parts": results
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity error: {str(e)}")