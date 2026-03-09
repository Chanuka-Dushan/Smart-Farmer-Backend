from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.blockchain_service import (
    register_part,
    verify_part,
    transfer_part
)

from utils.qr_service import generate_qr
from utils.qr_jwt_service import verify_qr_token

from utils.parts_repository import (
    update_blockchain_registration,
    get_part_metadata
)

router = APIRouter(
    prefix="/api/blockchain",
    tags=["Blockchain"]
)


# ==========================================
# REQUEST MODELS
# ==========================================

class TransferRequest(BaseModel):

    serialNumber: str
    newOwner: str


class QRVerifyRequest(BaseModel):

    qr_token: str


# ==========================================
# REGISTER PART IN BLOCKCHAIN
# ==========================================

@router.post("/register")
def register_blockchain(data: dict):

    try:

        serial = data["serialNumber"]

        # 🔴 CHECK METADATA FIRST
        metadata = get_part_metadata(serial)

        if not metadata:
            raise HTTPException(
                status_code=400,
                detail="Metadata must be registered first"
            )

        # Register part in blockchain
        result = register_part(data)

        tx_hash = result["tx_hash"]

        # Update DB with blockchain tx hash
        update_blockchain_registration(serial, tx_hash)

        # Generate QR code
        qr_image = generate_qr(serial, tx_hash)

        return StreamingResponse(
            qr_image,
            media_type="image/png"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================================
# VERIFY PART FROM BLOCKCHAIN
# ==========================================

@router.get("/verify/{serial}")

def verify_blockchain_part(serial: str):

    try:

        blockchain_data = verify_part(serial)

        if not blockchain_data:

            return {
                "status": "FAKE",
                "message": "Part not found on blockchain"
            }

        metadata = get_part_metadata(serial)

        return {
            "status": "AUTHENTIC",
            "serialNumber": serial,
            "blockchainData": blockchain_data,
            "metadata": metadata
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# VERIFY PART USING QR
# ==========================================

@router.post("/verify-qr")

def verify_qr(request: QRVerifyRequest):

    try:

        decoded = verify_qr_token(request.qr_token)

        if not decoded:

            return {
                "status": "INVALID_QR"
            }

        serial = decoded["serial"]

        tx_hash = decoded["tx_hash"]

        blockchain_data = verify_part(serial)

        if not blockchain_data:

            return {
                "status": "FAKE"
            }

        metadata = get_part_metadata(serial)

        return {
            "status": "AUTHENTIC",
            "serialNumber": serial,
            "txHash": tx_hash,
            "blockchainData": blockchain_data,
            "metadata": metadata
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# TRANSFER OWNERSHIP
# ==========================================

@router.post("/transfer")

def transfer_ownership(request: TransferRequest):

    try:

        result = transfer_part(
            request.serialNumber,
            request.newOwner
        )

        return {
            "status": "SUCCESS",
            "message": "Ownership transferred",
            "serialNumber": request.serialNumber,
            "newOwner": request.newOwner,
            "txHash": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )