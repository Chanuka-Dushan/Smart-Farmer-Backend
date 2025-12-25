import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.requests import Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from dotenv import load_dotenv
from sqlalchemy import Integer, Boolean

# Load environment variables from .env file
load_dotenv()

# --- JWT Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 1. Smart Database Connection ---
# This looks for 'DATABASE_URL' in your environment (DigitalOcean).
# If it can't find it, it defaults to 'sqlite:///./users.db' (Local).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

# Fix for DigitalOcean's Postgres URL string format if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure the connection arguments based on the database type
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Database Models (The Tables) ---
class User(Base):
    """Admin User Model"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class AppUser(Base):
    """Mobile App User Model"""
    __tablename__ = "app_users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    fcm_token = Column(String(500), nullable=True)
    address = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

# Create the tables automatically
Base.metadata.create_all(bind=engine)

# --- 3. Pydantic Models (Input Validation) ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
    fcm_token: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# --- 3. Pydantic Models (Input Validation) ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
    fcm_token: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None  # 'admin' or 'app_user'

# Mobile App User Schemas
class AppUserRegister(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    fcm_token: Optional[str] = None

class AppUserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    fcm_token: Optional[str] = None

class AppUserResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    is_banned: bool
    is_deleted: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AdminUpdateUser(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class AdminProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class MessageResponse(BaseModel):
    message: str
    success: bool = True

# --- 4. Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper Functions ---
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request) -> dict:
    """Validate JWT token and return user data (for admins)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"email": token_data.email}

async def get_current_app_user(request: Request, db: Session = Depends(get_db)) -> AppUser:
    """Validate JWT token and return app user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type", "admin")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # For app users, verify they exist and are not banned/deleted
        if user_type == "app_user":
            app_user = db.query(AppUser).filter(
                AppUser.email == email,
                AppUser.is_deleted == False
            ).first()
            
            if not app_user:
                raise HTTPException(status_code=401, detail="User not found")
            
            if app_user.is_banned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account has been banned"
                )
            
            return app_user
        else:
            raise HTTPException(status_code=403, detail="Invalid user type")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- 5. API Endpoints ---
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["farmerlk.me", "www.farmerlk.me", "http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Smart Farmer Backend is Running!"}

@app.get("/health")
def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

# REGISTRATION ENDPOINT DISABLED - ADMIN ONLY LOGIN
# @app.post("/register")
# def register(user: UserRegister, db: Session = Depends(get_db)):
#     """
#     Register a new admin user
#     """
#     # Check if user already exists
#     existing_user = db.query(User).filter(User.email == user.email).first()
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
#     
#     # Hash password and create user
#     hashed_password = hash_password(user.password)
#     db_user = User(
#         name=user.name,
#         email=user.email,
#         hashed_password=hashed_password,
#         is_active=True
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     
#     return {
#         "message": "Admin user created successfully",
#         "name": user.name,
#         "email": user.email
#     }

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Admin login endpoint - validates against database
    Returns JWT token on successful login
    """
    # Query database for user
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    # Create JWT token with user_type
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "admin"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user.email}
    }

@app.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if a JWT token is valid"""
    return {
        "valid": True,
        "email": current_user["email"]
    }

@app.get("/me")
async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Get current logged-in admin information"""
    return {
        "email": current_user["email"],
        "role": "admin"
    }

# ============= MOBILE APP USER ENDPOINTS =============

@app.post("/api/users/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_app_user(user_data: AppUserRegister, db: Session = Depends(get_db)):
    """Register a new mobile app user"""
    # Check if email already exists
    existing_user = db.query(AppUser).filter(
        AppUser.email == user_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if existing_user:
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
        data={"sub": new_user.email, "user_type": "app_user"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "firstname": new_user.firstname,
            "lastname": new_user.lastname
        }
    }

@app.post("/api/users/login", response_model=Token)
def login_app_user(login_data: UserLogin, db: Session = Depends(get_db)):
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
            detail="Your account has been banned. Please contact support."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "app_user"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname
        }
    }

@app.get("/api/users/me", response_model=AppUserResponse)
async def get_my_profile(current_user: AppUser = Depends(get_current_app_user)):
    """Get current user's profile"""
    return current_user

@app.put("/api/users/me", response_model=AppUserResponse)
async def update_my_profile(
    update_data: AppUserUpdate,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
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
    
    current_user.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(current_user)
    
    return current_user

@app.put("/api/users/me/password", response_model=MessageResponse)
async def update_my_password(
    password_data: PasswordUpdate,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Update current user's password"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(message="Password updated successfully", success=True)

@app.delete("/api/users/me", response_model=MessageResponse)
async def delete_my_account(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Soft delete current user's account"""
    current_user.is_deleted = True
    db.commit()
    
    return MessageResponse(message="Account deleted successfully", success=True)

# ============= ADMIN USER MANAGEMENT ENDPOINTS =============

@app.put("/admin/profile", response_model=dict)
async def update_admin_profile(
    update_data: AdminProfileUpdate,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update admin profile through dashboard"""
    admin = db.query(User).filter(User.email == current_admin["email"]).first()
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Check if email is being changed and if it's already taken
    if update_data.email and update_data.email != admin.email:
        existing_admin = db.query(User).filter(User.email == update_data.email).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        admin.email = update_data.email
    
    if update_data.name is not None:
        admin.name = update_data.name
    
    db.commit()
    db.refresh(admin)
    
    return {
        "id": admin.id,
        "name": admin.name,
        "email": admin.email,
        "is_active": admin.is_active
    }

@app.put("/admin/password", response_model=MessageResponse)
async def update_admin_password(
    password_data: PasswordUpdate,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update admin password"""
    admin = db.query(User).filter(User.email == current_admin["email"]).first()
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not verify_password(password_data.old_password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    admin.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(message="Admin password updated successfully", success=True)

@app.get("/admin/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    include_deleted: bool = False,
    include_banned: bool = True,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users for dashboard view (Admin only)"""
    from sqlalchemy import or_
    
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
    users = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "is_banned": user.is_banned,
            "is_deleted": user.is_deleted,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        for user in users
    ]

@app.get("/admin/users/stats")
async def get_user_stats(
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard (Admin only)"""
    from sqlalchemy import func
    
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
        "total_users": total_users or 0,
        "active_users": active_users or 0,
        "banned_users": banned_users or 0,
        "deleted_users": deleted_users or 0
    }

@app.get("/admin/users/{user_id}", response_model=AppUserResponse)
async def get_user_by_id(
    user_id: int,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user details by ID (Admin only)"""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user

@app.put("/admin/users/{user_id}", response_model=AppUserResponse)
async def update_user(
    user_id: int,
    update_data: AdminUpdateUser,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information (Admin only)"""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
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
    
    user.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(user)
    
    return user

@app.put("/admin/users/{user_id}/ban", response_model=AppUserResponse)
async def ban_unban_user(
    user_id: int,
    is_banned: bool,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ban or unban a user (Admin only)"""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_banned = is_banned
    user.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/admin/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    permanent: bool = False,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user (Admin only)"""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if permanent:
        # Permanent deletion
        db.delete(user)
        db.commit()
        return MessageResponse(message="User permanently deleted", success=True)
    else:
        # Soft deletion
        user.is_deleted = True
        user.updated_at = datetime.now(timezone.utc).isoformat()
        db.commit()
        return MessageResponse(message="User soft deleted", success=True)

# Entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)