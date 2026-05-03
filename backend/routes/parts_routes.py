from fastapi import APIRouter, HTTPException

from utils.parts_repository import (
    save_part_metadata,
    get_part_metadata,
    get_all_parts
)

router = APIRouter(
    prefix="/api/metadata",
    tags=["Parts Metadata"]
)


# -----------------------------------------
# REGISTER PART METADATA
# -----------------------------------------

@router.post("/register")

def register_part_metadata(data: dict):

    try:

        save_part_metadata(data)

        return {
            "message": "Part metadata saved"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------------
# GET PART BY SERIAL
# -----------------------------------------

@router.get("/{serial}")

def get_part(serial: str):

    part = get_part_metadata(serial)

    if not part:

        raise HTTPException(
            status_code=404,
            detail="Part not found"
        )

    return part


# -----------------------------------------
# GET ALL PARTS
# -----------------------------------------

@router.get("/")

def get_all():

    return get_all_parts()