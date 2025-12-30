from pydantic import BaseModel, EmailStr, Field
from typing import Optional
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
