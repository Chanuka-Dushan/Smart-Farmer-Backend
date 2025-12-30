import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from dotenv import load_dotenv
from sqlalchemy import Integer, Boolean, Text, DateTime

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
    profile_picture_url = Column(String(500), nullable=True)
    google_id = Column(String(255), nullable=True)
    facebook_id = Column(String(255), nullable=True)
    is_social_login = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

class PasswordReset(Base):
    """Password Reset Token Model"""
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Seller(Base):
    """Seller Model"""
    __tablename__ = "sellers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    business_name = Column(String(255), nullable=False)
    owner_firstname = Column(String(100), nullable=False)
    owner_lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    business_address = Column(Text, nullable=True)
    business_description = Column(Text, nullable=True)
    # Location fields
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    shop_location_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    fcm_token = Column(String(500), nullable=True)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

class Notification(Base):
    """Notification Model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    user_type = Column(String(50), nullable=False)  # 'app_user', 'seller', 'all'
    target_user_id = Column(Integer, nullable=True)  # Specific user ID, null for broadcast
    sent_by = Column(Integer, nullable=False)  # Admin ID who sent the notification
    is_sent = Column(Boolean, default=False)
    sent_at = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

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
    user_type: Optional[str] = 'buyer'
    business_name: Optional[str] = None
    business_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    shop_location_name: Optional[str] = None

class AppUserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None
    fcm_token: Optional[str] = None

class SocialLoginRequest(BaseModel):
    email: str
    firstname: str
    lastname: str
    social_id: str
    provider: str
    profile_picture_url: Optional[str] = None
    fcm_token: Optional[str] = None

class AppUserResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    profile_picture_url: Optional[str]
    is_social_login: bool
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

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# Seller Schemas
class SellerRegister(BaseModel):
    business_name: str
    owner_firstname: str
    owner_lastname: str
    email: str
    password: str
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    business_description: Optional[str] = None
    fcm_token: Optional[str] = None

class SellerUpdate(BaseModel):
    business_name: Optional[str] = None
    owner_firstname: Optional[str] = None
    owner_lastname: Optional[str] = None
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    business_description: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    shop_location_name: Optional[str] = None
    fcm_token: Optional[str] = None

class SellerResponse(BaseModel):
    id: int
    business_name: str
    owner_firstname: str
    owner_lastname: str
    email: str
    phone_number: Optional[str]
    business_address: Optional[str]
    business_description: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    shop_location_name: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AdminUpdateSeller(BaseModel):
    business_name: Optional[str] = None
    owner_firstname: Optional[str] = None
    owner_lastname: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    business_description: Optional[str] = None

# Notification Schemas
class NotificationCreate(BaseModel):
    title: str
    message: str
    user_type: str  # 'app_user', 'seller', 'all'
    target_user_id: Optional[int] = None  # Specific user ID, null for broadcast

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    user_type: str
    target_user_id: Optional[int]
    sent_by: int
    is_sent: bool
    sent_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

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

async def get_current_seller(request: Request, db: Session = Depends(get_db)) -> Seller:
    """Validate JWT token and return seller"""
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
        
        # For sellers, verify they exist and are active
        if user_type == "seller":
            seller = db.query(Seller).filter(
                Seller.email == email,
                Seller.is_active == True
            ).first()
            
            if not seller:
                raise HTTPException(status_code=401, detail="Seller not found")
            
            return seller
        else:
            raise HTTPException(status_code=403, detail="Invalid user type")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

# Mount static files for profile pictures
os.makedirs("uploads/profile_pictures", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

# ============= SELLER ENDPOINTS =============

@app.post("/api/sellers/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_seller(seller_data: SellerRegister, db: Session = Depends(get_db)):
    """Register a new seller"""
    # Check if email already exists
    existing_seller = db.query(Seller).filter(
        Seller.email == seller_data.email
    ).first()
    
    if existing_seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new seller
    hashed_password = hash_password(seller_data.password)
    new_seller = Seller(
        business_name=seller_data.business_name,
        owner_firstname=seller_data.owner_firstname,
        owner_lastname=seller_data.owner_lastname,
        email=seller_data.email,
        hashed_password=hashed_password,
        phone_number=seller_data.phone_number,
        business_address=seller_data.business_address,
        business_description=seller_data.business_description,
        fcm_token=seller_data.fcm_token,
        is_verified=False,
        is_active=True
    )
    
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_seller.email, "user_type": "seller"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_seller.id,
            "email": new_seller.email,
            "business_name": new_seller.business_name,
            "owner_firstname": new_seller.owner_firstname,
            "owner_lastname": new_seller.owner_lastname
        }
    }

@app.post("/api/sellers/login", response_model=Token)
def login_seller(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login for sellers"""
    # Find seller
    seller = db.query(Seller).filter(
        Seller.email == login_data.email,
        Seller.is_active == True
    ).first()
    
    if not seller or not verify_password(login_data.password, seller.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": seller.email, "user_type": "seller"},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": seller.id,
            "email": seller.email,
            "business_name": seller.business_name,
            "owner_firstname": seller.owner_firstname,
            "owner_lastname": seller.owner_lastname
        }
    }

@app.get("/api/sellers/me", response_model=SellerResponse)
async def get_my_seller_profile(current_seller: Seller = Depends(get_current_seller)):
    """Get current seller's profile"""
    return current_seller

@app.put("/api/sellers/me", response_model=SellerResponse)
async def update_my_seller_profile(
    update_data: SellerUpdate,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update current seller's profile"""
    if update_data.business_name is not None:
        current_seller.business_name = update_data.business_name
    if update_data.owner_firstname is not None:
        current_seller.owner_firstname = update_data.owner_firstname
    if update_data.owner_lastname is not None:
        current_seller.owner_lastname = update_data.owner_lastname
    if update_data.phone_number is not None:
        current_seller.phone_number = update_data.phone_number
    if update_data.business_address is not None:
        current_seller.business_address = update_data.business_address
    if update_data.business_description is not None:
        current_seller.business_description = update_data.business_description
    if update_data.fcm_token is not None:
        current_seller.fcm_token = update_data.fcm_token
    
    current_seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(current_seller)
    
    return current_seller

@app.put("/api/sellers/me/password", response_model=MessageResponse)
async def update_my_seller_password(
    password_data: PasswordUpdate,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update current seller's password"""
    if not verify_password(password_data.old_password, current_seller.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_seller.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(message="Password updated successfully", success=True)

@app.put("/api/sellers/me/location", response_model=SellerResponse)
async def update_seller_location(
    latitude: str,
    longitude: str,
    shop_location_name: Optional[str] = None,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update seller's shop location"""
    current_seller.latitude = latitude
    current_seller.longitude = longitude
    if shop_location_name is not None:
        current_seller.shop_location_name = shop_location_name
    
    current_seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(current_seller)
    
    return current_seller

@app.get("/api/sellers/locations")
async def get_seller_locations(
    db: Session = Depends(get_db)
):
    """Get all verified and active seller locations for map display"""
    sellers = db.query(Seller).filter(
        Seller.is_active == True,
        Seller.is_verified == True,
        Seller.latitude.isnot(None),
        Seller.longitude.isnot(None)
    ).all()
    
    return [
        {
            "id": seller.id,
            "business_name": seller.business_name,
            "latitude": seller.latitude,
            "longitude": seller.longitude,
            "shop_location_name": seller.shop_location_name,
            "business_address": seller.business_address,
            "phone_number": seller.phone_number,
            "business_description": seller.business_description,
        }
        for seller in sellers
    ]

# ============= NOTIFICATION ENDPOINTS =============

@app.post("/api/notifications/send", response_model=MessageResponse)
async def send_notification(
    notification_data: NotificationCreate,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification to users (Admin only)"""
    from fcm_utils import send_notification as fcm_send
    
    # Get admin ID
    admin = db.query(User).filter(User.email == current_admin["email"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Create notification record
    new_notification = Notification(
        title=notification_data.title,
        message=notification_data.message,
        user_type=notification_data.user_type,
        target_user_id=notification_data.target_user_id,
        sent_by=admin.id,
        is_sent=False
    )
    
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    # Send notifications based on user type
    success_count = 0
    total_count = 0
    
    if notification_data.user_type == "all":
        # Send to all app users and sellers
        app_users = db.query(AppUser).filter(
            AppUser.is_deleted == False,
            AppUser.is_banned == False,
            AppUser.fcm_token.isnot(None)
        ).all()
        
        sellers = db.query(Seller).filter(
            Seller.is_active == True,
            Seller.fcm_token.isnot(None)
        ).all()
        
        all_users = app_users + sellers
        total_count = len(all_users)
        
        for user in all_users:
            if hasattr(user, 'fcm_token') and user.fcm_token:
                result = fcm_send(
                    fcm_token=user.fcm_token,
                    title=notification_data.title,
                    body=notification_data.message
                )
                if "error" not in result:
                    success_count += 1
                    
    elif notification_data.user_type == "app_user":
        if notification_data.target_user_id:
            # Send to specific app user
            user = db.query(AppUser).filter(
                AppUser.id == notification_data.target_user_id,
                AppUser.is_deleted == False,
                AppUser.is_banned == False,
                AppUser.fcm_token.isnot(None)
            ).first()
            
            if user:
                total_count = 1
                result = fcm_send(
                    fcm_token=user.fcm_token,
                    title=notification_data.title,
                    body=notification_data.message
                )
                if "error" not in result:
                    success_count = 1
        else:
            # Send to all app users
            app_users = db.query(AppUser).filter(
                AppUser.is_deleted == False,
                AppUser.is_banned == False,
                AppUser.fcm_token.isnot(None)
            ).all()
            
            total_count = len(app_users)
            for user in app_users:
                result = fcm_send(
                    fcm_token=user.fcm_token,
                    title=notification_data.title,
                    body=notification_data.message
                )
                if "error" not in result:
                    success_count += 1
                    
    elif notification_data.user_type == "seller":
        if notification_data.target_user_id:
            # Send to specific seller
            seller = db.query(Seller).filter(
                Seller.id == notification_data.target_user_id,
                Seller.is_active == True,
                Seller.fcm_token.isnot(None)
            ).first()
            
            if seller:
                total_count = 1
                result = fcm_send(
                    fcm_token=seller.fcm_token,
                    title=notification_data.title,
                    body=notification_data.message
                )
                if "error" not in result:
                    success_count = 1
        else:
            # Send to all sellers
            sellers = db.query(Seller).filter(
                Seller.is_active == True,
                Seller.fcm_token.isnot(None)
            ).all()
            
            total_count = len(sellers)
            for seller in sellers:
                result = fcm_send(
                    fcm_token=seller.fcm_token,
                    title=notification_data.title,
                    body=notification_data.message
                )
                if "error" not in result:
                    success_count += 1
    
    # Update notification status
    new_notification.is_sent = True
    new_notification.sent_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    
    return MessageResponse(
        message=f"Notification sent to {success_count} out of {total_count} users",
        success=True
    )

@app.get("/api/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 100,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications (Admin only)"""
    notifications = db.query(Notification).offset(skip).limit(limit).all()
    return notifications

@app.get("/api/users/notifications")
async def get_user_notifications(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get notifications for current app user (placeholder - implement based on user notification history)"""
    # For now, return empty list - you can implement notification history later
    return []

@app.get("/api/sellers/notifications")
async def get_seller_notifications(
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get notifications for current seller (placeholder - implement based on seller notification history)"""
    # For now, return empty list - you can implement notification history later
    return []

@app.post("/api/users/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_app_user(user_data: AppUserRegister, db: Session = Depends(get_db)):
    """Register a new mobile app user"""
    email_lower = user_data.email.lower()
    
    # Check if email already exists in AppUser or Seller
    existing_user = db.query(AppUser).filter(
        func.lower(AppUser.email) == email_lower,
        AppUser.is_deleted == False
    ).first()
    
    if not existing_user:
        existing_user = db.query(Seller).filter(
            func.lower(Seller.email) == email_lower
        ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Register based on user type
    hashed_password = hash_password(user_data.password)
    user_type = user_data.user_type.lower() if user_data.user_type else 'buyer'
    
    if user_type == 'seller':
        # Create new seller
        new_seller = Seller(
            business_name=user_data.business_name or f"{user_data.firstname}'s Shop",
            owner_firstname=user_data.firstname,
            owner_lastname=user_data.lastname,
            email=email_lower,
            hashed_password=hashed_password,
            phone_number=user_data.phone_number,
            business_address=user_data.business_address,
            fcm_token=user_data.fcm_token,
            latitude=user_data.latitude,
            longitude=user_data.longitude,
            shop_location_name=user_data.shop_location_name
        )
        db.add(new_seller)
        db.commit()
        db.refresh(new_seller)
        
        # Create token for seller
        access_token = create_access_token(
            data={"sub": new_seller.email, "user_type": "seller"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_seller.id,
                "email": new_seller.email,
                "firstname": new_seller.owner_firstname,
                "lastname": new_seller.owner_lastname,
                "user_type": "seller"
            }
        }
    else:
        # Create new app user (buyer)
        new_user = AppUser(
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            email=email_lower,
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
        
        # Create token for buyer
        access_token = create_access_token(
            data={"sub": new_user.email, "user_type": "app_user"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "firstname": new_user.firstname,
                "lastname": new_user.lastname,
                "user_type": "buyer"
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

@app.post("/api/users/social-login", response_model=Token)
def social_login_app_user(login_data: SocialLoginRequest, db: Session = Depends(get_db)):
    """Social login for mobile app users (Google/Facebook)"""
    email_lower = login_data.email.lower()
    
    # 1. Search in AppUser (Buyer)
    user = db.query(AppUser).filter(
        func.lower(AppUser.email) == email_lower,
        AppUser.is_deleted == False
    ).first()
    
    user_type = "app_user"
    
    # 2. Search in Seller if not found in AppUser
    if not user:
        user = db.query(Seller).filter(
            func.lower(Seller.email) == email_lower
        ).first()
        if user:
            user_type = "seller"

    if not user:
        # Create new user if not exists (default to Buyer)
        user = AppUser(
            firstname=login_data.firstname,
            lastname=login_data.lastname,
            email=email_lower,
            hashed_password=hash_password(secrets.token_urlsafe(16)), 
            profile_picture_url=login_data.profile_picture_url,
            is_social_login=True,
            fcm_token=login_data.fcm_token
        )
        if login_data.provider == 'google':
            user.google_id = login_data.social_id
        else:
            user.facebook_id = login_data.social_id
            
        db.add(user)
        db.commit()
        db.refresh(user)
        user_type = "app_user"
    else:
        # Update social ID if not set
        if login_data.provider == 'google' and not user.google_id:
            user.google_id = login_data.social_id
        elif login_data.provider == 'facebook' and not user.facebook_id:
            user.facebook_id = login_data.social_id
            
        user.is_social_login = True
        if login_data.fcm_token:
            user.fcm_token = login_data.fcm_token
        db.commit()
    
    # Check if user is banned (if it's an AppUser)
    if hasattr(user, 'is_banned') and user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned. Please contact support."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user_type},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "firstname": user.firstname if user_type == "app_user" else user.owner_firstname,
            "lastname": user.lastname if user_type == "app_user" else user.owner_lastname,
            "user_type": "buyer" if user_type == "app_user" else "seller"
        }
    }

@app.post("/api/users/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset token"""
    user = db.query(AppUser).filter(AppUser.email == data.email, AppUser.is_deleted == False).first()
    if not user:
        # We don't want to reveal if a user exists or not for security reasons
        return MessageResponse(message="If your email is registered, you will receive a reset token.", success=True)
    
    # Generate token
    token = secrets.token_hex(3) # Short token for mobile ease, in production use longer hex
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Save token
    reset_record = PasswordReset(
        email=data.email,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_record)
    db.commit()
    
    # Send email
    # TODO: Integrate mail service. For now we just return it or print it.
    from utils.email_utils import send_password_reset_email
    send_password_reset_email(data.email, token)
    
    return MessageResponse(message="Password reset token sent to your email.", success=True)

@app.post("/api/users/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == data.token,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(AppUser).filter(AppUser.email == reset_record.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = hash_password(data.new_password)
    user.is_social_login = False # Now they have a password
    reset_record.is_used = True
    db.commit()
    
    return MessageResponse(message="Password reset successfully.", success=True)

@app.post("/api/users/me/profile-picture", response_model=AppUserResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Upload or update profile picture"""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create unique filename
    file_extension = file.filename.split(".")[-1]
    filename = f"user_{current_user.id}_{secrets.token_hex(8)}.{file_extension}"
    file_path = f"uploads/profile_pictures/{filename}"
    
    # Save file
    with open(f"backend/{file_path}", "wb") as buffer:
        buffer.write(await file.read())
    
    # Update user record
    # In production, use the actual domain
    current_user.profile_picture_url = f"/uploads/profile_pictures/{filename}"
    db.commit()
    db.refresh(current_user)
    
    return current_user

@app.delete("/api/users/me/profile-picture", response_model=AppUserResponse)
async def delete_profile_picture(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Delete profile picture"""
    current_user.profile_picture_url = None
    db.commit()
    db.refresh(current_user)
    
    return current_user

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
    if update_data.profile_picture_url is not None:
        current_user.profile_picture_url = update_data.profile_picture_url
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
            "profile_picture_url": user.profile_picture_url,
            "is_social_login": user.is_social_login,
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

# ============= ADMIN SELLER MANAGEMENT ENDPOINTS =============

@app.get("/admin/sellers")
async def get_all_sellers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    include_inactive: bool = False,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sellers for dashboard view (Admin only)"""
    from sqlalchemy import or_
    
    query = db.query(Seller)
    
    # Filter inactive sellers
    if not include_inactive:
        query = query.filter(Seller.is_active == True)
    
    # Search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Seller.business_name.ilike(search_filter),
                Seller.owner_firstname.ilike(search_filter),
                Seller.owner_lastname.ilike(search_filter),
                Seller.email.ilike(search_filter)
            )
        )
    
    # Get sellers with pagination
    sellers = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": seller.id,
            "business_name": seller.business_name,
            "owner_firstname": seller.owner_firstname,
            "owner_lastname": seller.owner_lastname,
            "email": seller.email,
            "phone_number": seller.phone_number,
            "business_address": seller.business_address,
            "business_description": seller.business_description,
            "is_verified": seller.is_verified,
            "is_active": seller.is_active,
            "created_at": seller.created_at,
            "updated_at": seller.updated_at
        }
        for seller in sellers
    ]

@app.get("/admin/sellers/stats")
async def get_seller_stats(
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get seller statistics for dashboard (Admin only)"""
    from sqlalchemy import func
    
    total_sellers = db.query(func.count(Seller.id)).scalar()
    active_sellers = db.query(func.count(Seller.id)).filter(
        Seller.is_active == True
    ).scalar()
    verified_sellers = db.query(func.count(Seller.id)).filter(
        Seller.is_verified == True,
        Seller.is_active == True
    ).scalar()
    
    return {
        "total_sellers": total_sellers or 0,
        "active_sellers": active_sellers or 0,
        "verified_sellers": verified_sellers or 0
    }

@app.get("/admin/sellers/{seller_id}", response_model=SellerResponse)
async def get_seller_by_id(
    seller_id: int,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific seller details by ID (Admin only)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    return seller

@app.put("/admin/sellers/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: int,
    update_data: AdminUpdateSeller,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update seller information (Admin only)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    # Check if email is being changed and if it's already taken
    if update_data.email and update_data.email != seller.email:
        existing_seller = db.query(Seller).filter(
            Seller.email == update_data.email
        ).first()
        if existing_seller:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        seller.email = update_data.email
    
    # Update other fields if provided
    if update_data.business_name is not None:
        seller.business_name = update_data.business_name
    if update_data.owner_firstname is not None:
        seller.owner_firstname = update_data.owner_firstname
    if update_data.owner_lastname is not None:
        seller.owner_lastname = update_data.owner_lastname
    if update_data.phone_number is not None:
        seller.phone_number = update_data.phone_number
    if update_data.business_address is not None:
        seller.business_address = update_data.business_address
    if update_data.business_description is not None:
        seller.business_description = update_data.business_description
    
    seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(seller)
    
    return seller

@app.put("/admin/sellers/{seller_id}/verify", response_model=SellerResponse)
async def verify_seller(
    seller_id: int,
    is_verified: bool,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify or unverify a seller (Admin only)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    seller.is_verified = is_verified
    seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(seller)
    
    return seller

@app.put("/admin/sellers/{seller_id}/activate", response_model=SellerResponse)
async def activate_deactivate_seller(
    seller_id: int,
    is_active: bool,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a seller (Admin only)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    seller.is_active = is_active
    seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(seller)
    
    return seller

@app.delete("/admin/sellers/{seller_id}", response_model=MessageResponse)
async def delete_seller(
    seller_id: int,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a seller (Admin only)"""
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    # Permanent deletion
    db.delete(seller)
    db.commit()
    
    return MessageResponse(message="Seller deleted successfully", success=True)

# Entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)