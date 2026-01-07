from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.user import AppUser
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    UserPasswordUpdateRequest,
    UserResponse,
    UserLoginResponse,
    MessageResponse
)
from utils.database import get_db
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/users", tags=["Mobile App Users"])

@router.post("/register", response_model=UserLoginResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new mobile app user
    
    - **firstname**: User's first name
    - **lastname**: User's last name
    - **email**: User's email (must be unique)
    - **password**: User's password (minimum 6 characters)
    - **phone_number**: Optional phone number
    - **address**: Optional address
    - **fcm_token**: Optional FCM token for push notifications
    """
    # Check if email already exists
    existing_user = db.query(AppUser).filter(
        AppUser.email == user_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if existing_user:
        # If social login and user exists, treat as login (return token)
        if user_data.is_social_login:
            # Update social ID if missing
            if user_data.google_id and not existing_user.google_id:
                existing_user.google_id = user_data.google_id
                db.commit()
            if user_data.facebook_id and not existing_user.facebook_id:
                existing_user.facebook_id = user_data.facebook_id
                db.commit()

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": existing_user.email, "user_type": "user"},
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
        is_deleted=False,
        is_banned=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "user_type": "user"},
        expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )

@router.post("/login", response_model=UserLoginResponse)
def login_user(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Login for mobile app users
    
    - **email**: User's email
    - **password**: User's password
    
    Returns JWT token and user information
    """
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
            detail="Your account has been banned. Please contact support."
        )
    
    # Update FCM token if provided
    if login_data.fcm_token:
        user.fcm_token = login_data.fcm_token
        db.commit()
        db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user"},
        expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: AppUser = Depends(get_current_user)):
    """
    Get current user's profile
    
    Requires authentication token in header: Authorization: Bearer <token>
    """
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
def update_my_profile(
    update_data: UserUpdateRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    
    - **firstname**: Update first name
    - **lastname**: Update last name
    - **phone_number**: Update phone number
    - **address**: Update address
    - **fcm_token**: Update FCM token for notifications
    
    Requires authentication token in header: Authorization: Bearer <token>
    """
    # Update only provided fields
    if update_data.firstname is not None:
        current_user.firstname = update_data.firstname
    if update_data.lastname is not None:
        current_user.lastname = update_data.lastname
    if update_data.phone_number is not None:
        current_user.phone_number = update_data.phone_number
    if update_data.address is not None:
        current_user.address = update_data.address
    if update_data.fcm_token is not None:
        current_user.fcm_token = update_data.fcm_token
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)

@router.put("/me/password", response_model=MessageResponse)
def update_my_password(
    password_data: UserPasswordUpdateRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's password
    
    - **old_password**: Current password for verification
    - **new_password**: New password (minimum 6 characters)
    
    Requires authentication token in header: Authorization: Bearer <token>
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(
        message="Password updated successfully",
        success=True
    )

@router.delete("/me", response_model=MessageResponse)
def delete_my_account(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete current user's account
    
    This marks the account as deleted but doesn't remove it from the database.
    
    Requires authentication token in header: Authorization: Bearer <token>
    """
    current_user.is_deleted = True
    db.commit()
    
    return MessageResponse(
        message="Account deleted successfully",
        success=True
    )
