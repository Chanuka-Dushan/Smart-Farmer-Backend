from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services.tyre_service import get_tyre_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict")
async def predict_tyre(image: UploadFile = File(...)):
    """Accept image multipart and return tyre inspection results."""
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image uploaded")

    contents = await image.read()
    svc = get_tyre_service()

    try:
        result = svc.predict_from_bytes(contents, return_overlay=True)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Tyre prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
