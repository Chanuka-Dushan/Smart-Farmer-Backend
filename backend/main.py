import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from starlette.requests import Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from dotenv import load_dotenv
from sqlalchemy import Integer, Boolean, Text, DateTime

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin SDK early
try:
    from fcm_utils import initialize_firebase_admin
    firebase_initialized = initialize_firebase_admin()
    if firebase_initialized:
        print("✓ Firebase Admin SDK initialized successfully")
    else:
        print("⚠ Firebase Admin SDK initialization failed")
except ImportError:
    print("⚠ Firebase Admin SDK not available")
    firebase_initialized = False

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
    is_social_login = Column(Boolean, default=False)
    google_id = Column(String(100), nullable=True)
    facebook_id = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat(), onupdate=lambda: datetime.now(timezone.utc).isoformat())

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

class SparePartRequest(Base):
    """Spare Part Request Model"""
    __tablename__ = "spare_part_requests"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # FK to app_users
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    status = Column(String(50), default="active")  # active, completed, cancelled
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

class SparePartOffer(Base):
    """Spare Part Offer Model"""
    __tablename__ = "spare_part_offers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, nullable=False)  # FK to spare_part_requests
    seller_id = Column(Integer, nullable=False)  # FK to sellers
    price = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, accepted, rejected
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

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
    profile_picture_url: Optional[str] = None
    is_social_login: bool = False
    google_id: Optional[str] = None
    facebook_id: Optional[str] = None

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

# Spare Parts Models
class SparePartRequestCreate(BaseModel):
    title: str
    description: str
    image_url: Optional[str] = None

class SparePartOfferCreate(BaseModel):
    price: str
    description: str

class SparePartOfferUpdate(BaseModel):
    status: str  # accepted, rejected

class SparePartRequestResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    image_url: Optional[str]
    status: str
    created_at: str

class SparePartOfferResponse(BaseModel):
    id: int
    request_id: int
    seller_id: int
    price: str
    description: str
    status: str
    created_at: str
    seller: Optional[dict] = None

# Social Login Models
class SocialLoginRequest(BaseModel):
    email: str
    firstname: str
    lastname: str
    social_id: str
    provider: str  # 'google' or 'facebook'
    profile_picture_url: Optional[str] = None
    fcm_token: Optional[str] = None

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

@app.get("/api/notifications/status")
async def check_notification_status():
    """Check Firebase Admin SDK initialization status"""
    try:
        from fcm_utils import initialize_firebase_admin, FIREBASE_ADMIN_AVAILABLE
        
        if not FIREBASE_ADMIN_AVAILABLE:
            return {
                "firebase_available": False,
                "error": "Firebase Admin SDK not installed. Run: pip install firebase-admin"
            }
        
        firebase_initialized = initialize_firebase_admin()
        
        return {
            "firebase_available": FIREBASE_ADMIN_AVAILABLE,
            "firebase_initialized": firebase_initialized,
            "status": "ready" if firebase_initialized else "configuration_needed"
        }
    except Exception as e:
        return {
            "firebase_available": False,
            "firebase_initialized": False,
            "error": str(e),
            "status": "error"
        }

@app.post("/api/notifications/send", response_model=MessageResponse)
async def send_notification_endpoint(
    notification_data: NotificationCreate,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification to users with enhanced error handling and validation (Admin only)"""
    try:
        from fcm_utils import send_notification as fcm_send, send_multicast_notification, logger, validate_fcm_config
        
        # Check Firebase configuration first
        if not validate_fcm_config():
            raise HTTPException(
                status_code=500, 
                detail="Firebase is not properly configured. Please check your Firebase Admin SDK credentials."
            )
        
        # Validate input
        if not notification_data.title or not notification_data.title.strip():
            raise HTTPException(status_code=400, detail="Notification title is required")
        
        if not notification_data.message or not notification_data.message.strip():
            raise HTTPException(status_code=400, detail="Notification message is required")
        
        if notification_data.user_type not in ["all", "app_user", "seller"]:
            raise HTTPException(status_code=400, detail="Invalid user_type. Must be 'all', 'app_user', or 'seller'")
        
        # Get admin ID
        admin = db.query(User).filter(User.email == current_admin["email"]).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Create notification record
        new_notification = Notification(
            title=notification_data.title.strip(),
            message=notification_data.message.strip(),
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
        error_details = []
        
        try:
            if notification_data.user_type == "all":
                # Send to all app users and sellers
                app_users = db.query(AppUser).filter(
                    AppUser.is_deleted == False,
                    AppUser.is_banned == False,
                    AppUser.fcm_token.isnot(None),
                    AppUser.fcm_token != ''
                ).all()
                
                sellers = db.query(Seller).filter(
                    Seller.is_active == True,
                    Seller.fcm_token.isnot(None),
                    Seller.fcm_token != ''
                ).all()
                
                all_tokens = []
                if app_users:
                    all_tokens.extend([user.fcm_token for user in app_users])
                if sellers:
                    all_tokens.extend([seller.fcm_token for seller in sellers])
                
                total_count = len(all_tokens)
                
                if all_tokens:
                    multicast_success, multicast_result = send_multicast_notification(
                        fcm_tokens=all_tokens,
                        title=notification_data.title,
                        body=notification_data.message,
                        data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                    )
                    
                    if multicast_success:
                        success_count = multicast_result.get('total_success', 0)
                    else:
                        error_details.append(f"Multicast error: {multicast_result.get('error', 'Unknown error')}")
                        
            elif notification_data.user_type == "app_user":
                if notification_data.target_user_id:
                    # Send to specific app user
                    user = db.query(AppUser).filter(
                        AppUser.id == notification_data.target_user_id,
                        AppUser.is_deleted == False,
                        AppUser.is_banned == False,
                        AppUser.fcm_token.isnot(None),
                        AppUser.fcm_token != ''
                    ).first()
                    
                    if user and user.fcm_token:
                        total_count = 1
                        send_success, send_result = fcm_send(
                            fcm_token=user.fcm_token,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_notification', 'notification_id': str(new_notification.id)}
                        )
                        
                        if send_success:
                            success_count = 1
                        else:
                            error_details.append(f"FCM error: {send_result.get('error', 'Unknown error')}")
                    else:
                        raise HTTPException(status_code=404, detail="User not found or no valid FCM token")
                else:
                    # Send to all app users
                    app_users = db.query(AppUser).filter(
                        AppUser.is_deleted == False,
                        AppUser.is_banned == False,
                        AppUser.fcm_token.isnot(None),
                        AppUser.fcm_token != ''
                    ).all()
                    
                    if app_users:
                        user_tokens = [user.fcm_token for user in app_users]
                        total_count = len(user_tokens)
                        
                        multicast_success, multicast_result = send_multicast_notification(
                            fcm_tokens=user_tokens,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                        )
                        
                        if multicast_success:
                            success_count = multicast_result.get('total_success', 0)
                        else:
                            error_details.append(f"Multicast error: {multicast_result.get('error', 'Unknown error')}")
                            
            elif notification_data.user_type == "seller":
                if notification_data.target_user_id:
                    # Send to specific seller
                    seller = db.query(Seller).filter(
                        Seller.id == notification_data.target_user_id,
                        Seller.is_active == True,
                        Seller.fcm_token.isnot(None),
                        Seller.fcm_token != ''
                    ).first()
                    
                    if seller and seller.fcm_token:
                        total_count = 1
                        send_success, send_result = fcm_send(
                            fcm_token=seller.fcm_token,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_notification', 'notification_id': str(new_notification.id)}
                        )
                        
                        if send_success:
                            success_count = 1
                        else:
                            error_details.append(f"FCM error: {send_result.get('error', 'Unknown error')}")
                    else:
                        raise HTTPException(status_code=404, detail="Seller not found or no valid FCM token")
                else:
                    # Send to all sellers
                    sellers = db.query(Seller).filter(
                        Seller.is_active == True,
                        Seller.fcm_token.isnot(None),
                        Seller.fcm_token != ''
                    ).all()
                    
                    if sellers:
                        seller_tokens = [seller.fcm_token for seller in sellers]
                        total_count = len(seller_tokens)
                        
                        multicast_success, multicast_result = send_multicast_notification(
                            fcm_tokens=seller_tokens,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                        )
                        
                        if multicast_success:
                            success_count = multicast_result.get('total_success', 0)
                        else:
                            error_details.append(f"Multicast error: {multicast_result.get('error', 'Unknown error')}")
            
            # Update notification record
            if success_count > 0:
                new_notification.is_sent = True
                new_notification.sent_at = datetime.now(timezone.utc).isoformat()
                db.commit()
                
                success_message = f"Notification sent successfully to {success_count}/{total_count} recipients"
                logger.info(success_message)
                
                if error_details:
                    success_message += f". Some errors occurred: {'; '.join(error_details)}"
                
                return MessageResponse(message=success_message, success=True)
            else:
                error_message = f"Failed to send notification to any recipients"
                if error_details:
                    error_message += f": {'; '.join(error_details)}"
                    
                logger.error(error_message)
                raise HTTPException(status_code=500, detail=error_message)
                
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Notification sending error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Notification endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing notification")


# ============= SELLER MANAGEMENT ENDPOINTS =============

@app.get("/api/admin/sellers", dependencies=[Depends(get_current_user)])
async def get_all_sellers(db: Session = Depends(get_db)):
    """Get all sellers (Admin only)"""
    try:
        sellers = db.query(Seller).all()
        return [
            {
                "id": seller.id,
                "business_name": seller.business_name,
                "email": seller.email,
                "business_address": seller.business_address,
                "phone_number": seller.phone_number,
                "business_description": seller.business_description,
                "is_active": seller.is_active,
                "created_at": seller.created_at,
            }
            for seller in sellers
        ]
    except Exception as e:
        logger.error(f"Error fetching sellers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch sellers")


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

# ============= MOBILE APP AUTH ENDPOINTS (FLUTTER COMPATIBLE) =============

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def auth_register(user_data: AppUserRegister, db: Session = Depends(get_db)):
    """Register for mobile app users (Flutter compatible endpoint)"""
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

            access_token = create_access_token(
                data={"sub": existing_user.email, "user_type": "user", "user_id": existing_user.id}
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "firstname": existing_user.firstname,
                    "lastname": existing_user.lastname
                }
            }

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
        profile_picture_url=user_data.profile_picture_url,
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
    access_token = create_access_token(
        data={"sub": new_user.email, "user_type": "user", "user_id": new_user.id}
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

@app.post("/api/auth/login", response_model=Token)
def auth_login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login for mobile app users (Flutter compatible endpoint)"""
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
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user", "user_id": user.id}
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

@app.post("/api/auth/social", response_model=Token)
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
        user.updated_at = datetime.now(timezone.utc).isoformat()
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
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user", "user_id": user.id}
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

@app.post("/api/auth/logout", response_model=MessageResponse)
async def auth_logout():
    """Logout for mobile app users (Flutter compatible endpoint)"""
    # For JWT tokens, logout is handled on client side by removing the token
    return MessageResponse(message="Logged out successfully", success=True)

# ============= USER PROFILE ENDPOINTS =============

@app.get("/api/users/me", response_model=AppUserResponse)
def get_my_profile(current_user: AppUser = Depends(get_current_app_user)):
    """Get current user's profile"""
    return current_user

@app.put("/api/users/me", response_model=AppUserResponse)
def update_my_profile(
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
def update_my_password(
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
def delete_my_account(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Soft delete current user's account"""
    current_user.is_deleted = True
    current_user.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    
    return MessageResponse(message="Account deleted successfully", success=True)

# ============= SPARE PARTS ENDPOINTS =============

@app.get("/api/spare-parts/requests", response_model=list[SparePartRequestResponse])
async def get_spare_part_requests(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get all active spare part requests"""
    requests = db.query(SparePartRequest).filter(SparePartRequest.status == "active").all()
    return requests

@app.get("/api/spare-parts/my-requests", response_model=list[SparePartRequestResponse])
async def get_my_spare_part_requests(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get current user's spare part requests"""
    requests = db.query(SparePartRequest).filter(SparePartRequest.user_id == current_user.id).all()
    return requests

@app.post("/api/spare-parts/requests", response_model=SparePartRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_spare_part_request(
    request_data: SparePartRequestCreate,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Create a new spare part request"""
    new_request = SparePartRequest(
        user_id=current_user.id,
        title=request_data.title,
        description=request_data.description,
        image_url=request_data.image_url,
        status="active"
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    return new_request

@app.get("/api/spare-parts/requests/{request_id}/offers", response_model=list[SparePartOfferResponse])
async def get_request_offers(
    request_id: int,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get offers for a specific spare part request"""
    # Verify request exists and belongs to user
    request = db.query(SparePartRequest).filter(SparePartRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these offers")
    
    offers = db.query(SparePartOffer).filter(SparePartOffer.request_id == request_id).all()
    
    # Add seller information to each offer
    result = []
    for offer in offers:
        seller = db.query(Seller).filter(Seller.id == offer.seller_id).first()
        offer_dict = {
            "id": offer.id,
            "request_id": offer.request_id,
            "seller_id": offer.seller_id,
            "price": offer.price,
            "description": offer.description,
            "status": offer.status,
            "created_at": offer.created_at,
            "seller": {
                "id": seller.id,
                "business_name": seller.business_name,
                "owner_firstname": seller.owner_firstname,
                "owner_lastname": seller.owner_lastname
            } if seller else None
        }
        result.append(offer_dict)
    
    return result

@app.post("/api/spare-parts/requests/{request_id}/offers", response_model=SparePartOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    request_id: int,
    offer_data: SparePartOfferCreate,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Create an offer for a spare part request (Seller only)"""
    # Verify request exists
    request = db.query(SparePartRequest).filter(SparePartRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request.status != "active":
        raise HTTPException(status_code=400, detail="Request is no longer active")
    
    new_offer = SparePartOffer(
        request_id=request_id,
        seller_id=current_seller.id,
        price=offer_data.price,
        description=offer_data.description,
        status="pending"
    )
    
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    
    return new_offer

@app.put("/api/spare-parts/offers/{offer_id}/status", response_model=MessageResponse)
async def update_offer_status(
    offer_id: int,
    status_data: SparePartOfferUpdate,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Accept or reject an offer (User only)"""
    offer = db.query(SparePartOffer).filter(SparePartOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Verify the request belongs to the current user
    request = db.query(SparePartRequest).filter(SparePartRequest.id == offer.request_id).first()
    if not request or request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this offer")
    
    if status_data.status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")
    
    offer.status = status_data.status
    offer.updated_at = datetime.now(timezone.utc).isoformat()
    
    # If offer is accepted, mark the request as completed
    if status_data.status == "accepted":
        request.status = "completed"
        request.updated_at = datetime.now(timezone.utc).isoformat()
    
    db.commit()
    
    return MessageResponse(message=f"Offer {status_data.status} successfully", success=True)

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

# ============= ADMIN SELLER MANAGEMENT ENDPOINTS =============

@app.get("/admin/sellers")
async def get_all_sellers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    include_inactive: bool = True,
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