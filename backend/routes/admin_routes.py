from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from models.user import Admin, AppUser
from models.schemas import (
    UserResponse,
    AdminUserUpdateRequest,
    AdminBanUserRequest,
    AdminProfileUpdateRequest,
    AdminPasswordUpdateRequest,
    AdminResponse,
    MessageResponse,
    UserLoginRequest,
    Token
)
from utils.database import get_db
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# ============= Admin Authentication =============

@router.post("/login", response_model=Token)
def admin_login(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Admin login endpoint
    
    - **email**: Admin email
    - **password**: Admin password
    
    Returns JWT token for admin access
    """
    # Find admin
    admin = db.query(Admin).filter(
        Admin.email == login_data.email,
        Admin.is_active == True
    ).first()
    
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.email, "user_type": "admin"},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    )

@router.get("/me", response_model=AdminResponse)
def get_admin_profile(current_admin: Admin = Depends(get_current_admin)):
    """
    Get current admin's profile
    
    Requires admin authentication token
    """
    return AdminResponse.from_orm(current_admin)

@router.put("/me", response_model=AdminResponse)
def update_admin_profile(
    update_data: AdminProfileUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update admin profile through dashboard
    
    - **name**: Update admin name
    - **email**: Update admin email (must be unique)
    
    Requires admin authentication token
    """
    # Check if email is being changed and if it's already taken
    if update_data.email and update_data.email != current_admin.email:
        existing_admin = db.query(Admin).filter(Admin.email == update_data.email).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_admin.email = update_data.email
    
    # Update name if provided
    if update_data.name is not None:
        current_admin.name = update_data.name
    
    db.commit()
    db.refresh(current_admin)
    
    return AdminResponse.from_orm(current_admin)

@router.put("/me/password", response_model=MessageResponse)
def update_admin_password(
    password_data: AdminPasswordUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update admin password
    
    - **old_password**: Current password for verification
    - **new_password**: New password (minimum 6 characters)
    
    Requires admin authentication token
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_admin.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(
        message="Admin password updated successfully",
        success=True
    )

# ============= User Management (Dashboard) =============

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    include_deleted: bool = Query(False, description="Include deleted users"),
    include_banned: bool = Query(True, description="Include banned users"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users for dashboard view
    
    - **skip**: Pagination offset
    - **limit**: Maximum results per page
    - **search**: Search by firstname, lastname, or email
    - **include_deleted**: Whether to include soft-deleted users
    - **include_banned**: Whether to include banned users
    
    Requires admin authentication token
    """
    query = db.query(AppUser)
    
    # Filter deleted users
    if not include_deleted:
        query = query.filter(AppUser.is_deleted == False)
    
    # Filter banned users
    if not include_banned:
        query = query.filter(AppUser.is_banned == False)
    
    # Search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                AppUser.firstname.ilike(search_filter),
                AppUser.lastname.ilike(search_filter),
                AppUser.email.ilike(search_filter)
            )
        )
    
    # Get users with pagination
    users = query.order_by(AppUser.created_at.desc()).offset(skip).limit(limit).all()
    
    return [UserResponse.from_orm(user) for user in users]

@router.get("/users/stats")
def get_user_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get user statistics for dashboard
    
    Returns counts of total, active, banned, and deleted users
    
    Requires admin authentication token
    """
    total_users = db.query(func.count(AppUser.id)).scalar()
    active_users = db.query(func.count(AppUser.id)).filter(
        AppUser.is_deleted == False,
        AppUser.is_banned == False
    ).scalar()
    banned_users = db.query(func.count(AppUser.id)).filter(
        AppUser.is_banned == True,
        AppUser.is_deleted == False
    ).scalar()
    deleted_users = db.query(func.count(AppUser.id)).filter(
        AppUser.is_deleted == True
    ).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "deleted_users": deleted_users
    }

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get specific user details by ID
    
    Requires admin authentication token
    """
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update_data: AdminUserUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information (Admin only)
    
    - **firstname**: Update first name
    - **lastname**: Update last name
    - **email**: Update email (must be unique)
    - **phone_number**: Update phone number
    - **address**: Update address
    
    Requires admin authentication token
    """
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email is being changed and if it's already taken
    if update_data.email and update_data.email != user.email:
        existing_user = db.query(AppUser).filter(
            AppUser.email == update_data.email,
            AppUser.is_deleted == False
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = update_data.email
    
    # Update other fields if provided
    if update_data.firstname is not None:
        user.firstname = update_data.firstname
    if update_data.lastname is not None:
        user.lastname = update_data.lastname
    if update_data.phone_number is not None:
        user.phone_number = update_data.phone_number
    if update_data.address is not None:
        user.address = update_data.address
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.put("/users/{user_id}/ban", response_model=UserResponse)
def ban_unban_user(
    user_id: int,
    ban_data: AdminBanUserRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Ban or unban a user (Admin only)
    
    - **is_banned**: True to ban, False to unban
    
    Requires admin authentication token
    """
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_banned = ban_data.is_banned
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    permanent: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user (Admin only)
    
    - **permanent**: If true, permanently deletes the user. If false, soft deletes (marks as deleted)
    
    Requires admin authentication token
    """
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if permanent:
        # Permanent deletion
        db.delete(user)
        db.commit()
        return MessageResponse(
            message="User permanently deleted",
            success=True
        )
    else:
        # Soft deletion
        user.is_deleted = True
        db.commit()
        return MessageResponse(
            message="User soft deleted (marked as deleted)",
            success=True
        )
