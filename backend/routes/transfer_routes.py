from fastapi import APIRouter, HTTPException

from utils.parts_repository import (
    request_transfer,
    get_pending_transfers,
    approve_transfer,
    get_part_metadata,
    normalize_owner_identifier
)

from utils.blockchain_service import transfer_part

router = APIRouter(
    prefix="/api/transfer",
    tags=["Ownership Transfer"]
)


# -----------------------------------------
# BUYER REQUESTS TRANSFER
# -----------------------------------------

@router.post("/request")
def request_transfer_route(data: dict):

    try:

        serial = data["serialNumber"]
        buyer = normalize_owner_identifier(data["buyer"])

        part = get_part_metadata(serial)

        if not part:
            raise HTTPException(
                status_code=404,
                detail="Part not found"
            )

        seller = normalize_owner_identifier(part["current_owner"])

        if seller == buyer:
            raise HTTPException(
                status_code=400,
                detail="Buyer cannot be the current owner"
            )

        # Save transfer request in DB
        request_transfer(serial, buyer)

        return {
            "message": "Transfer request sent to owner",
            "serialNumber": serial,
            "seller": seller,
            "requestedBuyer": buyer
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------------
# SELLER VIEW PENDING REQUESTS
# -----------------------------------------

@router.get("/pending/{seller}")
def pending_requests(seller: str):

    try:

        requests = get_pending_transfers(seller)

        return requests

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------------------
# SELLER APPROVES TRANSFER
# -----------------------------------------

@router.post("/approve")
def approve_transfer_route(data: dict):

    try:

        serial = data["serialNumber"]
        new_owner = normalize_owner_identifier(data["buyer"])

        part = get_part_metadata(serial)

        if not part:
            raise HTTPException(
                status_code=404,
                detail="Part not found"
            )

        if part["transfer_status"] != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="No pending transfer request"
            )

        requested_owner = normalize_owner_identifier(part.get("requested_new_owner"))

        if requested_owner and requested_owner != new_owner:
            raise HTTPException(
                status_code=400,
                detail="Buyer does not match the pending transfer request"
            )

        # Execute blockchain transfer
        result = transfer_part(serial, new_owner)

        tx_hash = result["tx_hash"]

        # Update database ownership
        approve_transfer(serial, new_owner)

        return {
            "message": "Ownership transferred successfully",
            "serialNumber": serial,
            "newOwner": new_owner,
            "txHash": tx_hash
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
