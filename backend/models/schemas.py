from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============= Mobile App User Schemas =============

class UserRegisterRequest(BaseModel):
    """Request model for user registration"""
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    fcm_token: Optional[str] = Field(None, max_length=500)
    is_social_login: bool = False
    google_id: Optional[str] = None
    facebook_id: Optional[str] = None

class UserLoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str
    fcm_token: Optional[str] = None

class SocialLoginRequest(BaseModel):
    """Request model for social login"""
    email: EmailStr
    firstname: str
    lastname: str
    social_id: str
    provider: str  # 'google' or 'facebook'
    profile_picture_url: Optional[str] = None
    fcm_token: Optional[str] = None

class UserUpdateRequest(BaseModel):
    """Request model for user profile update"""
    firstname: Optional[str] = Field(None, min_length=1, max_length=100)
    lastname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    fcm_token: Optional[str] = Field(None, max_length=500)

class UserPasswordUpdateRequest(BaseModel):
    """Request model for password update"""
    old_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    firstname: str
    lastname: str
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    profile_picture_url: Optional[str]
    is_social_login: bool
    is_banned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLoginResponse(BaseModel):
    """Response model for login"""
    access_token: str
    token_type: str
    user: UserResponse

# ============= Admin Dashboard Schemas =============

class AdminUserUpdateRequest(BaseModel):
    """Request model for admin to update user"""
    firstname: Optional[str] = Field(None, min_length=1, max_length=100)
    lastname: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)

class AdminBanUserRequest(BaseModel):
    """Request model for banning/unbanning user"""
    is_banned: bool

class AdminProfileUpdateRequest(BaseModel):
    """Request model for admin profile update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None

class AdminPasswordUpdateRequest(BaseModel):
    """Request model for admin password update"""
    old_password: str
    new_password: str = Field(..., min_length=6)

class AdminResponse(BaseModel):
    """Response model for admin data"""
    id: int
    name: Optional[str]
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdminSellerVerifyRequest(BaseModel):
    """Request model for verifying/unverifying seller"""
    is_verified: bool

class AdminSellerActivateRequest(BaseModel):
    """Request model for activating/deactivating seller"""
    is_active: bool

class SellerResponse(BaseModel):
    """Response model for seller data"""
    id: int
    business_name: str
    owner_firstname: str
    owner_lastname: str
    email: str
    phone_number: Optional[str]
    business_address: Optional[str]
    business_description: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============= Common Schemas =============

class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_type: Optional[str] = None  # 'admin' or 'user'

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True

class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Request model for reset password"""
    token: str
    new_password: str = Field(..., min_length=6)

# ================= Blockchain Schemas ==================

from pydantic import BaseModel, Field
from typing import Optional, List


# -------------------------------------------------------
# Register Part on Blockchain
# -------------------------------------------------------

class PartRegisterRequest(BaseModel):
    """Request body for registering a part on blockchain."""

    serial_number: str = Field(..., min_length=5)
    part_id: str
    manufacturer: str
    country: str
    owner: str
    minted_at: str
    refurbished: bool = False


# -------------------------------------------------------
# Blockchain Register Response
# -------------------------------------------------------

class BlockchainRegisterResponse(BaseModel):
    """Response after registering part in blockchain."""

    serial_number: str
    blockchain_tx_hash: str
    qr_generated: bool
    message: str


# -------------------------------------------------------
# Transfer Request (Handshake Step 1)
# -------------------------------------------------------

class TransferRequest(BaseModel):
    """Buyer requests ownership transfer."""

    serial_number: str
    buyer_id: int


# -------------------------------------------------------
# Transfer Approval (Handshake Step 2)
# -------------------------------------------------------

class TransferApprovalRequest(BaseModel):
    """Seller approves transfer request."""

    serial_number: str


# -------------------------------------------------------
# Blockchain Transfer Response
# -------------------------------------------------------

class TransferResponse(BaseModel):
    """Response after blockchain ownership transfer."""

    serial_number: str
    previous_owner: str
    new_owner: str
    blockchain_tx_hash: str
    message: str


# -------------------------------------------------------
# QR Verification Request
# -------------------------------------------------------

class QRVerifyRequest(BaseModel):
    """QR scan verification request."""

    qr_data: str


# -------------------------------------------------------
# Ledger History Entry
# -------------------------------------------------------

class PartHistoryEntry(BaseModel):
    """Single blockchain history record."""

    owner: str
    date: str
    tx_hash: Optional[str]


# -------------------------------------------------------
# Part Verification Response
# -------------------------------------------------------

class PartVerificationResponse(BaseModel):
    """Response returned when verifying a part."""

    status: str
    serial_number: str
    manufacturer: str
    current_owner: str
    blockchain_registered: bool
    history: List[PartHistoryEntry]


# -------------------------------------------------------
# Generic Message
# -------------------------------------------------------

class MessageResponse(BaseModel):
    """Generic API response."""

    message: str
    success: bool = True
class RatingRequest(BaseModel):
    """Request to submit a rating for a vendor/seller"""
    seller_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

# ============= Spare Parts / Compatibility Schemas (Tharushi's Component) =============

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from pydantic import BaseModel


# Shared fields
class PartBase(BaseModel):
    name: str
    brand: str
    machine_model: str

    description: Optional[str] = None
    category: Optional[str] = None

    diameter: Optional[float] = None
    material: Optional[str] = None

    price: float
    lifespan: Optional[int] = None

    specs_json: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None


# Create
class PartCreate(PartBase):
    """Request model to create a spare part"""
    pass


# Update (all optional)
class PartUpdate(BaseModel):
    """Request model to update a spare part (partial update allowed)"""
    name: Optional[str] = None
    brand: Optional[str] = None
    machine_model: Optional[str] = None

    description: Optional[str] = None
    category: Optional[str] = None

    diameter: Optional[float] = None
    material: Optional[str] = None

    price: Optional[float] = None
    lifespan: Optional[int] = None

    specs_json: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None


# Response
class PartResponse(PartBase):
    """Response model returned for a spare part"""
    id: int

    model_config = ConfigDict(from_attributes=True)


from pydantic import BaseModel, field_validator


from pydantic import BaseModel, field_validator


class FeedbackCreate(BaseModel):
    user_id: str
    part_id: int
    recommended_part_id: int
    feedback: str

    @field_validator("feedback")
    @classmethod
    def validate_feedback(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in ["accept", "reject"]:
            raise ValueError("feedback must be 'accept' or 'reject'")

        return value


class ForecastItemResponse(BaseModel):
    part_id: int
    part_name: str
    monthly_demand: List[int]
    forecast_next_month: float


class ReorderItemResponse(BaseModel):
    part_id: int
    part_name: str
    current_stock: int
    reorder_point: int
    forecast_next_month: float
    recommended_reorder_qty: int
    reason: str


class SubstituteSuggestionResponse(BaseModel):
    original_part_id: int
    original_part_name: str
    substitute_part_id: int
    substitute_part_name: str
    feedback_score: float
    reason: str


class InventoryRecommendResponse(BaseModel):
    reorder_list: List[ReorderItemResponse]
    suggested_substitutes: List[SubstituteSuggestionResponse]

