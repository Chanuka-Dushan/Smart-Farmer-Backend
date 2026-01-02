from datetime import timedelta, timezone, datetime
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.user import AppUser
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    SocialLoginRequest,
    UserLoginResponse,
    Token,
    MessageResponse,
    UserResponse
)
from utils.database import get_db
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserLoginResponse, status_code=status.HTTP_201_CREATED)
def auth_register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register for mobile app users"""
    # Check if email already exists
    existing_user = db.query(AppUser).filter(
        AppUser.email == user_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if existing_user:
        # Check if it's a social login (explicit flag or implicitly via password pattern from mobile app)
        is_mobile_social_login = user_data.password.startswith('social_')
        
        if user_data.is_social_login or is_mobile_social_login:
            # Update social ID if missing
            if user_data.google_id and not existing_user.google_id:
                existing_user.google_id = user_data.google_id
                db.commit()
            if user_data.facebook_id and not existing_user.facebook_id:
                existing_user.facebook_id = user_data.facebook_id
                db.commit()
            
            # Use the existing user's data
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": existing_user.email, "user_type": "user", "user_id": existing_user.id},
                expires_delta=access_token_expires
            )
            return UserLoginResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse.from_orm(existing_user)
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = AppUser(
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        email=user_data.email,
        hashed_password=hashed_password,
        phone_number=user_data.phone_number,
        address=user_data.address,
        fcm_token=user_data.fcm_token,
        is_social_login=user_data.is_social_login,
        google_id=user_data.google_id,
        facebook_id=user_data.facebook_id,
        is_deleted=False,
        is_banned=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "user_type": "user", "user_id": new_user.id},
        expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )

@router.post("/login", response_model=UserLoginResponse)
def auth_login(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """Login for mobile app users"""
    # Find user
    user = db.query(AppUser).filter(
        AppUser.email == login_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is banned
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user", "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.post("/social", response_model=UserLoginResponse)
def social_login(social_data: SocialLoginRequest, db: Session = Depends(get_db)):
    """Social login for mobile app users (Google/Facebook)"""
    # Check if user already exists
    user = db.query(AppUser).filter(
        AppUser.email == social_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if user:
        # Update user's FCM token and profile picture if provided
        if social_data.fcm_token:
            user.fcm_token = social_data.fcm_token
        if social_data.profile_picture_url:
            user.profile_picture_url = social_data.profile_picture_url
        # Update social IDs
        if social_data.provider == "google":
            user.google_id = social_data.social_id
        elif social_data.provider == "facebook":
            user.facebook_id = social_data.social_id
        user.is_social_login = True
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
    else:
        # Create new user for social login
        user = AppUser(
            firstname=social_data.firstname,
            lastname=social_data.lastname,
            email=social_data.email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # Random password for social users
            profile_picture_url=social_data.profile_picture_url,
            fcm_token=social_data.fcm_token,
            is_social_login=True,
            google_id=social_data.social_id if social_data.provider == "google" else None,
            facebook_id=social_data.social_id if social_data.provider == "facebook" else None,
            is_deleted=False,
            is_banned=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user", "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.post("/logout", response_model=MessageResponse)
def auth_logout():
    """Logout for mobile app users"""
    return MessageResponse(message="Logged out successfully", success=True)
