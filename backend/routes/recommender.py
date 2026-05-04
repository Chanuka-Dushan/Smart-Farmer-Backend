from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

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


def _find_parts_table(db: Session):
    """
    Finds the table that contains spare part data.
    This avoids changing your existing recommender logic.
    It looks for a table with machine_model and an id/part_id column.
    """
    inspector = inspect(db.bind)

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        column_names = {col["name"] for col in columns}

        has_machine_model = "machine_model" in column_names
        has_id = "id" in column_names or "part_id" in column_names

        if has_machine_model and has_id:
            return table_name, column_names

    return None, set()


def _get_machine_model_by_part_id(db: Session, part_id: int):
    """
    Gets machine_model for a recommended part ID.
    Works whether your table uses id or part_id.
    """
    if not part_id:
        return None

    table_name, column_names = _find_parts_table(db)

    if not table_name:
        return None

    id_column = "part_id" if "part_id" in column_names else "id"

    query = text(
        f"""
        SELECT machine_model
        FROM {table_name}
        WHERE {id_column} = :part_id
        LIMIT 1
        """
    )

    result = db.execute(query, {"part_id": part_id}).fetchone()

    if not result:
        return None

    return result[0]


def _attach_machine_model_to_recommendations(db: Session, response):
    """
    Adds machine_model to each recommendation item if missing.
    Keeps your existing response structure unchanged.
    """
    if not isinstance(response, dict):
        return response

    recommendations = response.get("recommendations")

    if not isinstance(recommendations, list):
        return response

    for item in recommendations:
        if not isinstance(item, dict):
            continue

        # Do not overwrite if recommender already sends machine_model
        if item.get("machine_model"):
            continue

        recommended_part_id = (
            item.get("recommended_part")
            or item.get("recommended_part_id")
            or item.get("part_id")
            or item.get("id")
        )

        machine_model = _get_machine_model_by_part_id(
            db=db,
            part_id=recommended_part_id,
        )

        if machine_model:
            item["machine_model"] = machine_model

    return response


@router.get("/recommend/{part_id}")
def get_recommendations(
    part_id: int,
    top_k: int = Query(5, ge=1, le=20),
    mode: str = Query("normal", pattern="^(normal|before_after)$"),
    db: Session = Depends(get_db)
):
    try:
        response = recommend_parts(
            db=db,
            part_id=part_id,
            top_k=top_k,
            mode=mode
        )

        response = _attach_machine_model_to_recommendations(
            db=db,
            response=response,
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))