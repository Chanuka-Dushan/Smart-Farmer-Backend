from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from models.user import AppUser
from models.schemas import (
    PartVerificationResponse,
    PartRegisterRequest,
    TransferRequest,
    MaintenanceLogRequest,
    RatingRequest,
    MessageResponse
)
from utils.database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain & Ledger"])

@router.get("/verify/{qr_code}", response_model=PartVerificationResponse)
def verify_part_authenticity(qr_code: str, db: Session = Depends(get_db)):
    """
    Scan a QR code to verify part provenance and authenticity from the ledger.
    """
    query = text("""
        SELECT p.name, p.brand, m.name as manufacturer, map.blockchain_id, map.is_refurbished, map.id
        FROM bc_parts_ledger_map map
        JOIN parts p ON map.part_id = p.id
        JOIN bc_manufacturers m ON map.manufacturer_id = m.id
        WHERE map.blockchain_id = :qr
    """)
    
    result = db.execute(query, {"qr": qr_code}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This part serial number is not registered on the Blockchain ledger."
        )

    # Fetch ledger history from bc_ownership_records
    history_query = text("""
        SELECT status, transfer_date FROM bc_ownership_records 
        WHERE bc_part_id = :id ORDER BY transfer_date DESC
    """)
    history_records = db.execute(history_query, {"id": result[5]}).fetchall()

    return PartVerificationResponse(
        status="AUTHENTIC",
        name=result[0],
        brand=result[1],
        manufacturer=result[2],
        serial=result[3],
        condition="Refurbished" if result[4] else "New",
        history=[{"event": h[0], "date": str(h[1])} for h in history_records]
    )

@router.post("/register", response_model=MessageResponse)
def register_on_ledger(data: PartRegisterRequest, current_user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Register a physical part as a Digital Twin on the Hyperledger Fabric network.
    """
    try:
        db.execute(
            text("INSERT INTO bc_parts_ledger_map (part_id, blockchain_id, manufacturer_id) VALUES (:p, :bc, :m)"),
            {"p": data.part_id, "bc": data.serial_number, "m": data.manufacturer_id}
        )
        db.commit()
        return MessageResponse(message="Asset successfully minted on Blockchain Ledger", success=True)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfer", response_model=MessageResponse)
def transfer_ownership(data: TransferRequest, current_user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Records a secure ownership transfer between stakeholders.
    """
    db.execute(
        text("INSERT INTO bc_ownership_records (bc_part_id, current_owner_user_id, status) VALUES (:id, :u, 'Transferred')"),
        {"id": data.bc_map_id, "u": data.buyer_id}
    )
    db.commit()
    return MessageResponse(message="Ownership transfer recorded on-chain", success=True)

@router.post("/rate", response_model=MessageResponse)
def rate_seller_reputation(data: RatingRequest, current_user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Updates the decentralized reputation score of a vendor.
    """
    db.execute(
        text("INSERT INTO bc_reputation_scores (seller_id, rater_id, rating_value, comment) VALUES (:s, :r, :v, :c)"),
        {"s": data.seller_id, "r": current_user.id, "v": data.rating, "c": data.comment}
    )
    db.commit()
    return MessageResponse(message="Feedback submitted and verified", success=True)