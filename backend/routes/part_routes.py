from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db_session import SessionLocal
from models.part import Part

router = APIRouter(
    prefix="/api/parts",
    tags=["Parts"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/machine-models")
def get_machine_models(db: Session = Depends(get_db)):
    results = (
        db.query(Part.machine_model)
        .filter(Part.machine_model.isnot(None))
        .distinct()
        .all()
    )

    machine_models = sorted([row[0] for row in results if row[0]])

    return {"machine_models": machine_models}