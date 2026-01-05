import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from dotenv import load_dotenv
from sqlalchemy import Integer, Boolean, Text, DateTime
import shutil
from pathlib import Path
import logging
try:
    import tensorflow as tf
    import numpy as np
    tensorflow_available = True
    print("✓ TensorFlow available")
except ImportError as e:
    tensorflow_available = False
    print(f"⚠ TensorFlow not available: {e}")
from io import BytesIO
from PIL import Image
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize Stripe
try:
    import stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        stripe_configured = True
        print("✓ Stripe configured")
    else:
        stripe_configured = False
        print("⚠ Stripe not configured - check STRIPE_SECRET_KEY")
except ImportError:
    stripe_configured = False
    print("⚠ Stripe library not available")
    stripe = None

# Initialize DigitalOcean Spaces
try:
    from spaces_utils import (
        upload_file_to_spaces,
        delete_file_from_spaces,
        generate_unique_filename,
        is_spaces_configured,
        get_content_type
    )
    spaces_configured = is_spaces_configured()
    if spaces_configured:
        print("✓ DigitalOcean Spaces configured")
    else:
        print("⚠ DigitalOcean Spaces not configured - check SPACES_KEY and SPACES_SECRET")
except ImportError as e:
    print(f"⚠ Spaces utils not available: {e}")
    spaces_configured = False

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
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days (30 * 24 * 60 minutes)

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
    logo_url = Column(String(500), nullable=True)
    # Location fields
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    shop_location_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
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

class SparePartOffer(Base):
    """Spare Part Offer Model"""
    __tablename__ = "spare_part_offers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, nullable=False)  # FK to spare_part_requests
    seller_id = Column(Integer, nullable=False)  # FK to sellers
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, accepted, rejected
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

class Payment(Base):
    """Payment Model for Spare Part Orders"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    offer_id = Column(Integer, nullable=False)  # FK to spare_part_offers
    user_id = Column(Integer, nullable=False)  # FK to app_users
    seller_id = Column(Integer, nullable=False)  # FK to sellers
    amount = Column(Float, nullable=False)  # Payment amount (5% of offer price)
    total_amount = Column(Float, nullable=False)  # Total offer amount
    stripe_payment_intent_id = Column(String(255), nullable=True)  # Stripe payment intent ID
    stripe_charge_id = Column(String(255), nullable=True)  # Stripe charge ID
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    payment_method = Column(String(50), default="stripe")  # stripe, etc.
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
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    shop_location_name: Optional[str] = None
    fcm_token: Optional[str] = None

class SellerUpdate(BaseModel):
    business_name: Optional[str] = None
    owner_firstname: Optional[str] = None
    owner_lastname: Optional[str] = None
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    business_description: Optional[str] = None
    logo_url: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    shop_location_name: Optional[str] = None
    fcm_token: Optional[str] = None

class SellerLocationUpdate(BaseModel):
    latitude: str
    longitude: str
    shop_location_name: Optional[str] = None

class SellerResponse(BaseModel):
    id: int
    business_name: str
    owner_firstname: str
    owner_lastname: str
    email: str
    phone_number: Optional[str]
    business_address: Optional[str]
    business_description: Optional[str]
    logo_url: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    shop_location_name: Optional[str]
    is_verified: bool
    is_active: bool
    onboarding_completed: bool
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
    price: float
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
    user: Optional[dict] = None  # Add user info

class SparePartOfferResponse(BaseModel):
    id: int
    request_id: int
    seller_id: int
    price: float
    description: str
    status: str

# Payment Models
class PaymentIntentCreate(BaseModel):
    offer_id: int

class PaymentConfirm(BaseModel):
    payment_intent_id: str

class PaymentResponse(BaseModel):
    id: int
    offer_id: int
    user_id: int
    seller_id: int
    amount: float
    total_amount: float
    stripe_payment_intent_id: Optional[str]
    stripe_charge_id: Optional[str]
    status: str
    payment_method: str
    created_at: str
    updated_at: str
    offer: Optional[dict] = None
    user: Optional[dict] = None
    seller: Optional[dict] = None

    class Config:
        from_attributes = True
    created_at: str
    seller: Optional[dict] = None
    request: Optional[dict] = None  # Add request info

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
        if user_type == "user":
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

async def get_current_user_or_seller(request: Request, db: Session = Depends(get_db)):
    """Validate JWT token and return either app user or seller"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header.strip() == "":
        logger.warning(f"Missing or empty Authorization header from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - Missing Authorization header",
        )
    
    try:
        parts = auth_header.split()
        if len(parts) != 2:
            logger.warning(f"Invalid authorization header format (expected 2 parts, got {len(parts)}): {auth_header[:50]}...")
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            logger.warning(f"Invalid authentication scheme: {scheme}")
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        if not token or token.strip() == "":
            logger.warning(f"Empty token provided")
            raise HTTPException(status_code=401, detail="Invalid token - token is empty")
    except ValueError as e:
        logger.warning(f"Error parsing authorization header: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type", "admin")
        
        if email is None:
            logger.warning("Token missing 'sub' field")
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Check if it's an admin
        if user_type == "admin":
            admin_user = db.query(User).filter(User.email == email).first()
            if not admin_user:
                logger.warning(f"Admin not found: {email}")
                raise HTTPException(status_code=401, detail="Admin not found")
            return {"type": "admin", "user": admin_user}
        
        # Check if it's a seller
        elif user_type == "seller":
            seller = db.query(Seller).filter(
                Seller.email == email,
                Seller.is_active == True
            ).first()
            
            if not seller:
                logger.warning(f"Seller not found or inactive: {email}")
                raise HTTPException(status_code=401, detail="Seller not found or inactive")
            
            return {"type": "seller", "user": seller}
        
        # Check if it's an app user
        elif user_type == "user":
            app_user = db.query(AppUser).filter(
                AppUser.email == email,
                AppUser.is_deleted == False
            ).first()
            
            if not app_user:
                logger.warning(f"User not found or deleted: {email}")
                raise HTTPException(status_code=401, detail="User not found or deleted")
            
            if app_user.is_banned:
                logger.warning(f"Banned user attempted access: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account has been banned"
                )
            
            return {"type": "user", "user": app_user}
        else:
            logger.warning(f"Invalid user_type in token: {user_type} for email: {email}")
            raise HTTPException(status_code=403, detail="Invalid user type")
            
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token error: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or malformed token")
    except JWTError as e:
        logger.warning(f"JWT decode error: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=401, detail="Token validation failed")

# --- 5. API Endpoints ---
app = FastAPI()

# --- AI Knowledge Integration ---
try:
    import ai_knowledge
    ai_available = True
    print("✓ AI Knowledge module loaded")
except ImportError as e:
    ai_available = False
    print(f"⚠ AI Knowledge not available: {e}")

# --- Weather API Configuration ---
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    logger.warning("⚠️ WEATHER_API_KEY not set - weather forecasting will be disabled")

# --- Vision# Model Configuration
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")
MODEL_PATH = os.getenv("MODEL_PATH", "smart_farmer_vision_v1.h5")  # Fixed: removed models/ prefix
MIN_PREDICTION_CONFIDENCE = float(os.getenv("MIN_PREDICTION_CONFIDENCE", "0.7"))

# Check if we should disable TensorFlow in production (for performance)
# Only disable if explicitly set via environment variable
# But also disable automatically in production environments for reliability
DISABLE_TENSORFLOW = (
    os.getenv("DISABLE_TENSORFLOW", "false").lower() == "true" or
    os.getenv("DYNO") is not None or  # Heroku
    os.getenv("RENDER") is not None or  # Render
    os.getenv("RAILWAY_ENVIRONMENT") is not None  # Railway
)

print(f"🔧 TensorFlow disabled: {DISABLE_TENSORFLOW}")

def download_model_from_spaces():
    """Download ML model from DigitalOcean Spaces if not present locally"""
    import requests
    from pathlib import Path
    
    # Check if model already exists
    if Path(MODEL_PATH).exists():
        logger.info(f"✓ Model already exists locally: {MODEL_PATH}")
        return True
    
    # Check if MODEL_URL is set
    model_url = os.getenv("MODEL_URL")
    if not model_url:
        logger.warning("⚠️ MODEL_URL not set - cannot download model from Spaces")
        return False
    
    try:
        logger.info(f"📥 Downloading model from Spaces: {model_url}")
        
        # Create models directory if needed
        Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        # Download model
        response = requests.get(model_url, timeout=60)
        response.raise_for_status()
        
        # Save model
        with open(MODEL_PATH, 'wb') as f:
            f.write(response.content)
        
        file_size = Path(MODEL_PATH).stat().st_size / 1024 / 1024
        logger.info(f"✅ Model downloaded successfully ({file_size:.2f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download model: {e}")
        return False

# Try to download model from Spaces if not present
if not DISABLE_TENSORFLOW and tensorflow_available:
    download_model_from_spaces()

# Load Vision Model
cnn_model = None
if tensorflow_available and not DISABLE_TENSORFLOW:
    try:
        # Disable TensorFlow warnings and optimize for production
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations that cause warnings

        cnn_model = tf.keras.models.load_model(MODEL_PATH)
        logger.info(f"✓ Vision Model Loaded: {MODEL_PATH}")
    except Exception as e:
        cnn_model = None
        print(f"⚠️ Vision Model Not Found ({e}). Using Simulation Mode.")
elif DISABLE_TENSORFLOW:
    print("⚠️ TensorFlow disabled for production performance. Using Simulation Mode.")
else:
    print("⚠️ TensorFlow not available. Using Simulation Mode for vision analysis.")

# --- Historical Stress Engine ---
def get_historical_stress_factor(location: str, part_name: str):
    """
    Calculates how much the part has suffered based on where the tractor lived.
    """
    loc = location.lower()
    part = part_name.lower()
    
    stress_factor = 1.0  # Default (1.0 = Normal aging)
    reason = "Normal Operating Conditions"

    # LOGIC A: DRY ZONE (Anuradhapura, Jaffna) -> Heat kills batteries & rubber
    if loc in ["anuradhapura", "jaffna", "polonnaruwa", "trincomalee"]:
        if "battery" in part or "belt" in part or "tire" in part:
            stress_factor = 1.25  # Aged 25% faster
            reason = "Dry Zone: High Heat accelerated material degradation"
        else:
            stress_factor = 1.10  # General dust/heat wear

    # LOGIC B: WET ZONE (Colombo, Galle) -> Humidity kills metal
    elif loc in ["colombo", "galle", "kandy", "ratnapura"]:
        if "pump" in part or "filter" in part or "clutch" in part or "piston" in part:
            stress_factor = 1.20  # Aged 20% faster
            reason = "Wet Zone: High Humidity accelerated corrosion/rust"

    return stress_factor, reason

# --- Future Risk Engine ---
def check_future_risk(location: str):
    """
    Checks the 5-Day Forecast. If storms are coming, risky parts get downgraded.
    """
    risk_penalty = 0.0
    risk_msg = "Forecast is stable."

    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            # Analyze next 5 data points (approx 15 hours)
            rain_found = False
            for item in data['list'][:5]:
                condition = item['weather'][0]['main'].lower()
                if "rain" in condition or "storm" in condition or "thunder" in condition:
                    rain_found = True
                break
            
            if rain_found:
                risk_penalty = 0.10  # 10% safety penalty
                risk_msg = "⚠️ WARNING: Storm Forecast. Failure risk elevated."
            else:
                risk_msg = "✅ Forecast: Clear skies. Low environmental risk."
        else:
            risk_msg = f"Weather API Unreachable (Status {response.status_code})"

    except Exception as e:
        print(f"Weather API Error: {e}")
        risk_msg = "⚠️ Offline Mode: Assuming Standard Risk"

    return risk_penalty, risk_msg

# --- Lifecycle Prediction Endpoint ---
@app.post("/api/predict-lifecycle")
async def predict_lifecycle(
    part_name: str = Form(...),
    usage_hours: Optional[float] = Form(None),
    location: str = Form(...),
    image: UploadFile = File(...) 
):
    """
    Predict remaining lifecycle of a tractor part
    
    Args:
        part_name: Name of the part (e.g., "battery", "fan belt")
        usage_hours: Hours the part has been used
        location: Geographic location (affects environmental stress)
        image: Image of the part for visual damage assessment
    
    Returns:
        JSON with prediction results including remaining life, status, and analysis
    """
    prediction_start_time = datetime.now(timezone.utc)
    
    try:
        usage_hours_value = float(usage_hours or 0.0)
        logger.info(f"📥 NEW REQUEST: {part_name} | Hours: {usage_hours} | Location: {location}")
        logger.info(f"📸 Image: {image.filename} ({image.content_type})")

        # Import ML utilities
        try:
            from ml_utils import ImagePreprocessor, PredictionValidator, clip_prediction
            from config import MIN_PREDICTION_CONFIDENCE
        except ImportError as e:
            logger.error(f"Failed to import ML utilities: {e}")
            raise HTTPException(status_code=500, detail="ML utilities not available")

        # Initialize validators
        image_preprocessor = ImagePreprocessor(target_size=(224, 224))
        prediction_validator = PredictionValidator(min_confidence=MIN_PREDICTION_CONFIDENCE)

        # A. GET FRESH LIFESPAN (From AI Knowledge / Gemini)
        if ai_available:
            fresh_life = ai_knowledge.get_standard_lifespan(part_name)
            logger.info(f"🤖 AI Knowledge: Available - Lifespan: {fresh_life} hours")
        else:
            fresh_life = 500  # Default fallback
            logger.warning(f"⚠️ AI Knowledge: Not available - Using fallback: {fresh_life} hours")

        # B. ANALYZE VISUAL DAMAGE (From .h5 Model)
        visual_damage = 0.0
        confidence = 0.0
        analysis_model = "Simulation Mode"
        
        # Read and validate image
        img_data = await image.read()
        logger.info(f"🖼️ Image data received: {len(img_data)} bytes")
        
        # Validate image
        is_valid_image, validation_message = image_preprocessor.validate_image(img_data)
        if not is_valid_image:
            logger.warning(f"⚠️ Image validation failed: {validation_message}")
            raise HTTPException(status_code=400, detail=f"Invalid image: {validation_message}")
        
        if cnn_model and tensorflow_available:
            try:
                # Preprocess image
                img_array = image_preprocessor.preprocess_image(img_data)
                if img_array is None:
                    raise ValueError("Image preprocessing failed")
                
                # Predict
                prediction = cnn_model.predict(img_array, verbose=0)
                raw_prediction = float(prediction[0][0])
                
                # Clip to valid range
                visual_damage = clip_prediction(raw_prediction, 0.0, 1.0)
                
                # Calculate confidence
                confidence = prediction_validator.calculate_confidence(visual_damage)
                
                # Validate prediction
                is_valid, validation_msg = prediction_validator.validate_prediction(
                    visual_damage, 
                    confidence
                )
                
                if not is_valid:
                    logger.warning(f"⚠️ Prediction validation warning: {validation_msg}")
                    # Continue but flag for review
                
                analysis_model = f"MobileNetV2 (Transfer Learning) - Confidence: {confidence:.2%}"
                logger.info(f"👁️ Vision Model: {int(visual_damage * 100)}% Damage (Confidence: {confidence:.2%})")
                
                # Log prediction for monitoring
                prediction_validator.log_prediction({
                    "part_name": part_name,
                    "prediction": visual_damage,
                    "confidence": confidence,
                    "raw_prediction": raw_prediction,
                    "location": location
                })
                
            except Exception as e:
                logger.error(f"❌ Vision model prediction failed: {e}")
                # Fall back to simulation
                visual_damage = 0.35
                confidence = 0.5
                analysis_model = "Simulation Mode (Model Error)"
                logger.warning("⚠️ Using simulation mode due to model error")
        else:
            # Fallback if TensorFlow not available or model not loaded
            logger.info("⚠️ Vision analysis unavailable. Using simulation mode.")
            visual_damage = 0.35
            confidence = 0.5
            analysis_model = "Simulation Mode"

        # C. ANALYZE TIME (Historical + Future)
        # 1. Past Stress
        hist_stress, hist_reason = get_historical_stress_factor(location, part_name)
        
        # 2. Future Risk
        future_penalty, future_msg = check_future_risk(location)

        # D. FINAL CALCULATION (The Master Formula)
        # Formula: Remaining = (Fresh_Life * (1 - Visual_Damage - Future_Risk)) - (Usage * Historical_Stress)
        
        # 1. Calculate Total Effective Capacity (Reduced by Damage & Risk)
        effective_capacity = fresh_life * (1.0 - visual_damage - future_penalty)
        
        # BONUS: If part is in good condition (< 20% damage), extend life by up to 30%
        # This accounts for well-maintained parts lasting longer than rated life
        condition_bonus_applied = 0.0
        if visual_damage < 0.20:  # Less than 20% damage
            condition_bonus = (0.20 - visual_damage) / 0.20 * 0.30  # Up to 30% bonus (reduced from 50%)
            effective_capacity *= (1.0 + condition_bonus)
            condition_bonus_applied = condition_bonus
            logger.info(f"✨ Condition Bonus: +{int(condition_bonus * 100)}% life extension")
        
        # 2. Calculate Real Usage (Inflated by Historical Stress)
        real_usage_impact = usage_hours_value * hist_stress
        
        # 3. Remaining Life
        remaining = effective_capacity - real_usage_impact
        remaining = max(0, int(remaining))  # No negative numbers
        
        # IMPORTANT: Cap remaining life to not exceed fresh lifespan
        # Even with bonuses, remaining life should never be more than the original rated life
        remaining = min(remaining, fresh_life)

        # E. DETERMINE STATUS COLOR
        status = "GOOD"
        color_code = "#008000"  # Green

        remaining_ratio = (remaining / fresh_life) if fresh_life else 0.0

        if remaining < 100 or visual_damage >= 0.85 or remaining_ratio <= 0.10:
            status = "CRITICAL REPLACEMENT"
            color_code = "#FF0000"  # Red
        elif remaining < 300 or visual_damage >= 0.65 or remaining_ratio <= 0.25:
            status = "WARNING"
            color_code = "#FFA500"  # Orange
        
        # Urgent Override: If Storm Coming AND Low Life
        if future_penalty > 0 and remaining < 400:
            status = "URGENT (STORM RISK)"
            color_code = "#FF4500"  # Red-Orange
        
        # F. CONVERT TO DAYS (8 hours per day of operation)
        HOURS_PER_DAY = 8
        fresh_life_days = round(fresh_life / HOURS_PER_DAY, 1)
        effective_capacity_days = round(effective_capacity / HOURS_PER_DAY, 1)
        real_usage_days = round(real_usage_impact / HOURS_PER_DAY, 1)
        remaining_days = round(remaining / HOURS_PER_DAY, 1)

        # G. RETURN JSON TO FLUTTER APP
        result = {
            "part_name": part_name,
            "ai_knowledge": {
                "fresh_lifespan": f"{fresh_life_days} Days ({fresh_life} hours)",
                "source": "Groq AI" if ai_available else "Simulation"
            },
            "visual_scan": {
                "wear_detected": f"{int(visual_damage * 100)}%",
                "confidence": f"{int(confidence * 100)}%",
                "analysis_model": analysis_model
            },
            "environment": {
                "location": location,
                "historical_stress": f"{hist_reason} (Load: {hist_stress}x)",
                "future_forecast": future_msg
            },
            "calculation": {
                "effective_capacity": f"{effective_capacity_days} Days ({int(effective_capacity)} hours)",
                "condition_bonus": f"+{int(condition_bonus_applied * 100)}%",
                "real_usage_impact": f"{real_usage_days} Days ({int(real_usage_impact)} hours)"
            },
            "prediction": {
                "remaining_life": f"{remaining_days} Days ({remaining} hours)",
                "remaining_life_hours": int(remaining),  # Add integer value for mobile app
                "estimated_life_hours": int(fresh_life),  # Add estimated life for mobile app
                "status": status,
                "color_code": color_code
            },
            "metadata": {
                "model_version": MODEL_VERSION,
                "prediction_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": int((datetime.now(timezone.utc) - prediction_start_time).total_seconds() * 1000)
            }
        }

        logger.info(f"✅ Prediction Complete: {status} | Remaining: {remaining_days} Days ({remaining} hours) | Time: {result['metadata']['processing_time_ms']}ms")
        
        # Log to database if enabled
        if os.getenv("ENABLE_PREDICTION_LOGGING", "true").lower() == "true":
            try:
                # TODO: Save to database for monitoring and analysis
                pass
            except Exception as e:
                logger.error(f"Failed to log prediction: {e}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Lifecycle Prediction Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )
if not spaces_configured:
    logger.warning("⚠ Spaces not configured - uploads will fail")
    # Keep local directories for fallback
    Path("uploads").mkdir(exist_ok=True)
    Path("uploads/spare-parts").mkdir(parents=True, exist_ok=True)
    Path("uploads/profile_pictures").mkdir(parents=True, exist_ok=True)
    # Mount static files for legacy URLs
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
else:
    logger.info("✓ Using DigitalOcean Spaces for image storage")

# Temporary admin endpoint to fix image paths
@app.post("/api/admin/fix-image-paths")
async def fix_image_paths_endpoint(db: Session = Depends(get_db)):
    """Fix incorrect image paths in database and move files to correct location"""
    import os
    
    # Ensure correct directory exists
    spare_parts_dir = Path("uploads/spare-parts")
    spare_parts_dir.mkdir(parents=True, exist_ok=True)
    
    # Move files from incorrect directories
    moved_count = 0
    old_dirs = [Path("uploads/spare_parts"), Path("spare_parts"), Path("spare-parts")]
    for old_dir in old_dirs:
        if old_dir.exists() and old_dir.is_dir():
            for file in old_dir.glob("*.jpg"):
                new_path = spare_parts_dir / file.name
                if not new_path.exists():
                    shutil.move(str(file), str(new_path))
                    logger.info(f"Moved file: {file.name}")
                    moved_count += 1
    
    # Fix database paths
    requests = db.query(SparePartRequest).filter(SparePartRequest.image_url.isnot(None)).all()
    fixed_count = 0
    
    for req in requests:
        if req.image_url:
            old_url = req.image_url
            
            # Fix various incorrect path formats
            if '/spare_parts/' in req.image_url:
                req.image_url = req.image_url.replace('/spare_parts/', '/uploads/spare-parts/')
                fixed_count += 1
            elif req.image_url.startswith('/uploads/spare_parts/'):
                req.image_url = req.image_url.replace('/uploads/spare_parts/', '/uploads/spare-parts/')
                fixed_count += 1
            elif req.image_url.startswith('/spare-parts/'):
                req.image_url = '/uploads' + req.image_url
                fixed_count += 1
            elif not req.image_url.startswith('/uploads/spare-parts/'):
                # Handle any other malformed path - extract filename and fix
                filename = os.path.basename(req.image_url)
                if filename:
                    req.image_url = f'/uploads/spare-parts/{filename}'
                    fixed_count += 1
            
            if req.image_url != old_url:
                logger.info(f"Fixed image path: {old_url} -> {req.image_url}")
    
    db.commit()
    
    return {
        "message": f"Fixed {fixed_count} image paths in database, moved {moved_count} files",
        "paths_fixed": fixed_count,
        "files_moved": moved_count,
        "success": True
    }

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

# ============= UNIFIED MOBILE LOGIN ENDPOINT =============

@app.post("/api/auth/unified-login", response_model=Token)
def unified_login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Unified login endpoint for mobile app
    Checks both app_users and sellers tables and returns appropriate user type
    """
    # First try to find in app_users
    app_user = db.query(AppUser).filter(
        AppUser.email == login_data.email,
        AppUser.is_deleted == False
    ).first()
    
    if app_user:
        # Verify password
        if not verify_password(login_data.password, app_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is banned
        if app_user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been suspended"
            )
        
        # Update FCM token if provided
        if login_data.fcm_token:
            app_user.fcm_token = login_data.fcm_token
            db.commit()
        
        # Create access token for app user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": app_user.email, "user_type": "user", "user_id": app_user.id},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": app_user.id,
                "email": app_user.email,
                "firstname": app_user.firstname,
                "lastname": app_user.lastname,
                "phone_number": app_user.phone_number,
                "address": app_user.address,
                "profile_picture_url": app_user.profile_picture_url,
                "is_social_login": app_user.is_social_login,
                "is_banned": app_user.is_banned,
                "user_type": "user"
            }
        }
    
    # If not found in app_users, try sellers
    seller = db.query(Seller).filter(
        Seller.email == login_data.email,
        Seller.is_active == True
    ).first()
    
    if seller:
        # Verify password
        if not verify_password(login_data.password, seller.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update FCM token if provided
        if login_data.fcm_token:
            seller.fcm_token = login_data.fcm_token
            db.commit()
        
        # Create access token for seller
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": seller.email, "user_type": "seller", "user_id": seller.id},
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
                "owner_lastname": seller.owner_lastname,
                "phone_number": seller.phone_number,
                "business_address": seller.business_address,
                "business_description": seller.business_description,
                "logo_url": seller.logo_url,
                "latitude": seller.latitude,
                "longitude": seller.longitude,
                "shop_location_name": seller.shop_location_name,
                "is_verified": seller.is_verified,
                "is_active": seller.is_active,
                "onboarding_completed": seller.onboarding_completed,
                "user_type": "seller"
            }
        }
    
    # If not found in either table
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

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
        latitude=seller_data.latitude,
        longitude=seller_data.longitude,
        shop_location_name=seller_data.shop_location_name,
        fcm_token=seller_data.fcm_token,
        is_verified=False,
        is_active=True,
        onboarding_completed=False if not seller_data.latitude or not seller_data.longitude else True
    )
    
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_seller.email, "user_type": "seller", "user_id": new_seller.id},
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
            "owner_lastname": new_seller.owner_lastname,
            "phone_number": new_seller.phone_number,
            "business_address": new_seller.business_address,
            "business_description": new_seller.business_description,
            "logo_url": new_seller.logo_url,
            "latitude": new_seller.latitude,
            "longitude": new_seller.longitude,
            "shop_location_name": new_seller.shop_location_name,
            "is_verified": new_seller.is_verified,
            "is_active": new_seller.is_active,
            "onboarding_completed": new_seller.onboarding_completed,
            "user_type": "seller"
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
    
    # Update FCM token if provided
    if login_data.fcm_token:
        seller.fcm_token = login_data.fcm_token
        db.commit()
    
    logger.info(f"Seller {seller.id} logged in - Logo URL: {seller.logo_url}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": seller.id,
            "email": seller.email,
            "business_name": seller.business_name,
            "owner_firstname": seller.owner_firstname,
            "owner_lastname": seller.owner_lastname,
            "phone_number": seller.phone_number,
            "business_address": seller.business_address,
            "business_description": seller.business_description,
            "logo_url": seller.logo_url,
            "latitude": seller.latitude,
            "longitude": seller.longitude,
            "shop_location_name": seller.shop_location_name,
            "is_verified": seller.is_verified,
            "is_active": seller.is_active,
            "onboarding_completed": seller.onboarding_completed
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
    if update_data.logo_url is not None:
        current_seller.logo_url = update_data.logo_url
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
    location_data: SellerLocationUpdate,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update seller's shop location"""
    current_seller.latitude = location_data.latitude
    current_seller.longitude = location_data.longitude
    if location_data.shop_location_name is not None:
        current_seller.shop_location_name = location_data.shop_location_name
    
    # Mark onboarding as completed when location is saved
    current_seller.onboarding_completed = True
    current_seller.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(current_seller)
    
    return current_seller

@app.get("/api/sellers/locations")
async def get_seller_locations(
    db: Session = Depends(get_db)
):
    """Get all active seller locations for map display (verified or not)"""
    # Debug logging
    total_sellers = db.query(Seller).count()
    active_sellers = db.query(Seller).filter(Seller.is_active == True).count()
    verified_sellers = db.query(Seller).filter(Seller.is_verified == True).count()
    with_coords = db.query(Seller).filter(
        Seller.latitude.isnot(None),
        Seller.longitude.isnot(None)
    ).count()
    
    logger.info(f"📊 Seller Stats: Total={total_sellers}, Active={active_sellers}, Verified={verified_sellers}, WithCoords={with_coords}")
    
    # Show ALL active sellers with coordinates (regardless of verification status)
    sellers = db.query(Seller).filter(
        Seller.is_active == True,
        Seller.latitude.isnot(None),
        Seller.longitude.isnot(None)
    ).all()
    
    logger.info(f"📍 Returning {len(sellers)} seller locations")
    if len(sellers) == 0:
        logger.warning("⚠️ No sellers found! Check: is_active=True, latitude!=NULL, longitude!=NULL")
        # List first 5 sellers with details for debugging
        all_sellers = db.query(Seller).limit(5).all()
        for s in all_sellers:
            logger.info(f"  Seller: {s.business_name} | Active={s.is_active} | Verified={s.is_verified} | Coords=({s.latitude},{s.longitude})")
    
    result = [
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
    
    logger.info(f"✅ Returning {len(result)} locations")
    return result

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
        from fcm_utils import send_notification as fcm_send, send_multicast_notification, validate_fcm_config
        
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
                    multicast_result = send_multicast_notification(
                        fcm_tokens=all_tokens,
                        title=notification_data.title,
                        body=notification_data.message,
                        data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                    )
                    
                    if multicast_result.get('success', False):
                        success_count = multicast_result.get('successful', 0)
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
                        
                        multicast_result = send_multicast_notification(
                            fcm_tokens=user_tokens,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                        )
                        
                        if multicast_result.get('success', False):
                            success_count = multicast_result.get('successful', 0)
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
                        
                        multicast_result = send_multicast_notification(
                            fcm_tokens=seller_tokens,
                            title=notification_data.title,
                            body=notification_data.message,
                            data={'type': 'admin_broadcast', 'notification_id': str(new_notification.id)}
                        )
                        
                        if multicast_result.get('success', False):
                            success_count = multicast_result.get('successful', 0)
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
    current_user_data: dict = Depends(get_current_user_or_seller),
    db: Session = Depends(get_db)
):
    """Get all notifications - accessible by users, sellers, and admins"""
    # Admins can see all notifications
    if current_user_data.get("type") == "admin":
        notifications = db.query(Notification).offset(skip).limit(limit).all()
        return notifications
    
    # Users and sellers see only notifications relevant to them
    user_type = current_user_data.get("type")
    if user_type == "seller":
        target_type = "seller"
    elif user_type == "user":
        target_type = "app_user"
    else:
        target_type = None
    
    # Get notifications for "all" or specific user type
    if target_type:
        notifications = db.query(Notification).filter(
            (Notification.user_type == "all") | (Notification.user_type == target_type)
        ).offset(skip).limit(limit).all()
    else:
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
            "lastname": new_user.lastname,
            "phone_number": new_user.phone_number,
            "address": new_user.address,
            "profile_picture_url": new_user.profile_picture_url,
            "is_social_login": new_user.is_social_login,
            "is_banned": new_user.is_banned,
            "is_deleted": new_user.is_deleted
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
    
    # Update FCM token if provided
    if login_data.fcm_token:
        user.fcm_token = login_data.fcm_token
        db.commit()
    
    logger.info(f"User {user.id} logged in - Profile picture: {user.profile_picture_url}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "phone_number": user.phone_number,
            "address": user.address,
            "profile_picture_url": user.profile_picture_url,
            "is_social_login": user.is_social_login,
            "is_banned": user.is_banned,
            "is_deleted": user.is_deleted
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

            access_token = create_access_token(
                data={"sub": existing_user.email, "user_type": "user", "user_id": existing_user.id}
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": AppUserResponse.from_orm(existing_user).dict()
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
        "user": AppUserResponse.from_orm(new_user).dict()
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
        "user": AppUserResponse.from_orm(user).dict()
    }

@app.post("/api/auth/social", response_model=Token)
def social_login(social_data: SocialLoginRequest, db: Session = Depends(get_db)):
    """Social login for mobile app users (Google/Facebook)"""
    # Check if email exists as seller first
    seller = db.query(Seller).filter(
        Seller.email == social_data.email,
        Seller.is_active == True
    ).first()
    
    if seller:
        # Update seller's FCM token and profile picture if provided
        if social_data.fcm_token:
            seller.fcm_token = social_data.fcm_token
        # Update social IDs
        if social_data.provider == "google":
            seller.google_id = social_data.social_id
        elif social_data.provider == "facebook":
            seller.facebook_id = social_data.social_id
        seller.is_social_login = True
        db.commit()
        db.refresh(seller)
        
        # Create access token for seller
        access_token = create_access_token(
            data={"sub": seller.email, "user_type": "seller", "user_id": seller.id}
        )
        
        logger.info(f"Seller {seller.id} social login - Logo URL: {seller.logo_url}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": SellerResponse.from_orm(seller).dict()
        }
    
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
    
    logger.info(f"User {user.id} social login - Profile picture: {user.profile_picture_url}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": AppUserResponse.from_orm(user).dict()
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

# ============= SELLER PROFILE ENDPOINTS =============

@app.get("/api/sellers/me", response_model=SellerResponse)
def get_my_seller_profile(current_seller: Seller = Depends(get_current_seller)):
    """Get current seller's profile"""
    return current_seller

@app.put("/api/sellers/me", response_model=SellerResponse)
def update_my_seller_profile(
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
def update_seller_password(
    password_data: PasswordUpdate,
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update seller's password"""
    if not verify_password(password_data.old_password, current_seller.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_seller.hashed_password = hash_password(password_data.new_password)
    db.commit()
    
    return MessageResponse(message="Password updated successfully", success=True)

# ============= SPARE PARTS ENDPOINTS =============

@app.post("/api/spare-parts/upload-image")
async def upload_spare_part_image(
    image: UploadFile = File(...)
):
    """Upload an image for spare part request (no auth required)"""
    try:
        logger.info(f"📸 Uploading spare part image: {image.filename}")
        logger.info(f"📄 Content type: {image.content_type}")
        
        # Validate file type - check both content_type and file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        is_valid_content = image.content_type and image.content_type.startswith('image/')
        is_valid_extension = any(image.filename.lower().endswith(ext) for ext in valid_extensions)
        
        if not is_valid_content and not is_valid_extension:
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        if not is_valid_content:
            logger.warning(f"⚠️ Content type not image/* but extension is valid: {image.filename}")
        
        # Validate file size (max 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        image_data = await image.read()
        if len(image_data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")
        
        # Generate unique filename
        file_ext = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"spare_part_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_ext}"
        
        # Upload to storage
        try:
            # Upload to Spaces if configured, otherwise save locally
            if spaces_configured:
                from spaces_utils import upload_file_to_spaces
                from io import BytesIO
                logger.info("🚀 Uploading to Digital Ocean Spaces...")
                
                image_io = BytesIO(image_data)
                image_url = upload_file_to_spaces(
                    image_io,
                    unique_filename,
                    content_type=image.content_type or 'image/jpeg',
                    folder="spare-parts"
                )
                
                if not image_url:
                    raise HTTPException(status_code=500, detail="Failed to upload to storage")
                    
                logger.info(f"✅ Image uploaded to Spaces: {image_url}")
            else:
                # Save locally
                logger.info("💾 Saving image locally...")
                upload_dir = Path("uploads/spare-parts")
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / unique_filename
                
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                image_url = f"{base_url}/uploads/spare-parts/{unique_filename}"
                logger.info(f"✅ Image saved locally: {image_url}")
        
        except Exception as e:
            logger.error(f"❌ Failed to upload image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
        
        return {"image_url": image_url, "message": "Image uploaded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during image upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@app.get("/api/spare-parts/requests", response_model=list[SparePartRequestResponse])
async def get_spare_part_requests(
    current_user_data: dict = Depends(get_current_user_or_seller),
    db: Session = Depends(get_db)
):
    """Get all spare part requests - accessible by users, sellers, and admins"""
    requests = db.query(SparePartRequest).all()
    
    # Add user information to each request
    result = []
    for req in requests:
        user = db.query(AppUser).filter(AppUser.id == req.user_id).first()
        
        # Handle created_at - it might already be a string or a datetime object
        created_at_str = None
        if req.created_at:
            if isinstance(req.created_at, str):
                created_at_str = req.created_at
            else:
                created_at_str = req.created_at.isoformat()
        
        req_dict = {
            "id": req.id,
            "user_id": req.user_id,
            "title": req.title,
            "description": req.description,
            "image_url": req.image_url if req.image_url else None,
            "status": req.status,
            "created_at": created_at_str,
            "user": {
                "id": user.id,
                "full_name": f"{user.firstname} {user.lastname}",
                "email": user.email,
                "phone": user.phone_number if user.phone_number else None,
                "profile_picture_url": user.profile_picture_url if user.profile_picture_url else None
            } if user else None
        }
        result.append(req_dict)
    
    return result

@app.get("/api/spare-parts/my-requests")
async def get_my_spare_part_requests(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get current user's spare part requests"""
    requests = db.query(SparePartRequest).filter(SparePartRequest.user_id == current_user.id).all()
    
    # Add user information to each request
    result = []
    for req in requests:
        # Handle created_at - it might already be a string or a datetime object
        created_at_str = None
        if req.created_at:
            if isinstance(req.created_at, str):
                created_at_str = req.created_at
            else:
                created_at_str = req.created_at.isoformat()
        
        req_dict = {
            "id": req.id,
            "user_id": req.user_id,
            "title": req.title,
            "description": req.description,
            "image_url": req.image_url if req.image_url else None,
            "status": req.status,
            "created_at": created_at_str,
            "user": {
                "id": current_user.id,
                "full_name": f"{current_user.firstname} {current_user.lastname}",
                "email": current_user.email,
                "phone": current_user.phone_number if current_user.phone_number else None,
                "profile_picture_url": current_user.profile_picture_url if current_user.profile_picture_url else None
            }
        }
        result.append(req_dict)
    
    return result

@app.post("/api/upload/spare-part-image")
async def upload_spare_part_image(
    file: UploadFile = File(...),
    current_user: AppUser = Depends(get_current_app_user),
):
    """Upload an image for a spare part request"""
    if not spaces_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload service not configured"
        )
    
    try:
        # Generate unique filename
        unique_filename = generate_unique_filename(current_user.id, file.filename)
        
        # Get content type
        content_type = get_content_type(file.filename)
        
        # Upload to Spaces
        file.file.seek(0)  # Reset file pointer
        image_url = upload_file_to_spaces(
            file.file,
            unique_filename,
            content_type=content_type,
            folder="spare-parts"
        )
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        
        logger.info(f"User {current_user.id} uploaded spare part image: {image_url}")
        return {"url": image_url, "image_url": image_url}
        
    except Exception as e:
        logger.error(f"Error uploading spare part image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

@app.post("/api/upload/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user_data: dict = Depends(get_current_user_or_seller),
    db: Session = Depends(get_db)
):
    """Upload profile picture for user or seller"""
    if not spaces_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload service not configured"
        )
    
    try:
        user_type = current_user_data["type"]
        user = current_user_data["user"]
        
        # Generate unique filename
        unique_filename = generate_unique_filename(user.id, file.filename)
        
        # Get content type
        content_type = get_content_type(file.filename)
        
        # Upload to Spaces
        file.file.seek(0)  # Reset file pointer
        
        # Use appropriate folder based on user type
        folder = "profile-pictures" if user_type == "user" else "seller-logos"
        
        image_url = upload_file_to_spaces(
            file.file,
            unique_filename,
            content_type=content_type,
            folder=folder
        )
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        
        # Update profile picture URL based on user type
        if user_type == "user":
            user.profile_picture_url = image_url
            logger.info(f"User {user.id} updated profile picture: {image_url}")
        elif user_type == "seller":
            user.logo_url = image_url
            logger.info(f"Seller {user.id} updated logo: {image_url}")
        
        db.commit()
        
        return {
            "url": image_url, 
            "image_url": image_url, 
            "profile_picture_url": image_url,
            "logo_url": image_url  # For sellers
        }
        
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )

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
                "owner_lastname": seller.owner_lastname,
                "latitude": seller.latitude,
                "longitude": seller.longitude,
                "shop_location_name": seller.shop_location_name
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
    
    # If offer is accepted, create a payment record (5% of offer price)
    if status_data.status == "accepted":
        request.status = "completed"
        request.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Calculate 5% deposit
        deposit_amount = offer.price * 0.05
        
        # Create payment record
        payment = Payment(
            offer_id=offer.id,
            user_id=current_user.id,
            seller_id=offer.seller_id,
            amount=deposit_amount,
            total_amount=offer.price,
            status="pending"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
    
    db.commit()
    
    return MessageResponse(message=f"Offer {status_data.status} successfully", success=True)

@app.get("/api/spare-parts/my-offers", response_model=list[SparePartOfferResponse])
async def get_my_offers(
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get all offers made by the current seller"""
    offers = db.query(SparePartOffer).filter(SparePartOffer.seller_id == current_seller.id).all()
    
    # Add request information to each offer
    result = []
    for offer in offers:
        request = db.query(SparePartRequest).filter(SparePartRequest.id == offer.request_id).first()
        
        # Handle created_at - it might be a string or datetime object
        created_at_str = None
        if offer.created_at:
            if isinstance(offer.created_at, str):
                created_at_str = offer.created_at
            else:
                created_at_str = offer.created_at.isoformat()
        
        offer_dict = {
            "id": offer.id,
            "request_id": offer.request_id,
            "seller_id": offer.seller_id,
            "price": offer.price,
            "description": offer.description,
            "status": offer.status,
            "created_at": created_at_str,
            "request": {
                "id": request.id,
                "title": request.title,
                "description": request.description,
                "image_url": request.image_url,
                "status": request.status
            } if request else None
        }
        result.append(offer_dict)
    
    return result


# ============= PAYMENT ENDPOINTS =============

@app.post("/api/payments/create-intent")
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe payment intent for 5% deposit"""
    if not stripe_configured or stripe is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not configured"
        )
    
    # Get the offer
    offer = db.query(SparePartOffer).filter(SparePartOffer.id == payment_data.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Verify the offer is accepted
    if offer.status != "accepted":
        raise HTTPException(status_code=400, detail="Offer must be accepted before payment")
    
    # Get or create payment record
    payment = db.query(Payment).filter(Payment.offer_id == offer.id).first()
    if not payment:
        # Calculate 5% deposit
        deposit_amount = offer.price * 0.05
        payment = Payment(
            offer_id=offer.id,
            user_id=current_user.id,
            seller_id=offer.seller_id,
            amount=deposit_amount,
            total_amount=offer.price,
            status="pending"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
    
    # Check if payment already completed
    if payment.status == "completed":
        raise HTTPException(status_code=400, detail="Payment already completed")
    
    try:
        # Create Stripe payment intent (amount in cents)
        intent = stripe.PaymentIntent.create(
            amount=int(payment.amount * 100),  # Convert to cents
            currency='usd',
            metadata={
                'payment_id': str(payment.id),
                'offer_id': str(offer.id),
                'user_id': str(current_user.id),
                'seller_id': str(offer.seller_id)
            }
        )
        
        # Update payment record with intent ID
        payment.stripe_payment_intent_id = intent.id
        db.commit()
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": payment.amount,
            "total_amount": payment.total_amount,
            "payment_id": payment.id
        }
    except Exception as e:
        logger.error(f"Stripe payment intent creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )

@app.post("/api/payments/confirm")
async def confirm_payment(
    payment_data: PaymentConfirm,
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Confirm payment completion"""
    if not stripe_configured or stripe is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service not configured"
        )
    
    try:
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_data.payment_intent_id)
        
        # Find payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_data.payment_intent_id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Verify payment belongs to current user
        if payment.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Check payment status
        if intent.status == 'succeeded':
            payment.status = "completed"
            payment.stripe_charge_id = intent.latest_charge if hasattr(intent, 'latest_charge') else None
            payment.updated_at = datetime.now(timezone.utc).isoformat()
            db.commit()
            
            return {
                "success": True,
                "message": "Payment confirmed successfully",
                "payment": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "status": payment.status
                }
            }
        else:
            payment.status = "failed"
            payment.updated_at = datetime.now(timezone.utc).isoformat()
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail=f"Payment not completed. Status: {intent.status}"
            )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Payment confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm payment: {str(e)}"
        )

@app.get("/api/payments/my-payments", response_model=list[PaymentResponse])
async def get_my_payments(
    current_user: AppUser = Depends(get_current_app_user),
    db: Session = Depends(get_db)
):
    """Get all payments for the current user"""
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    
    result = []
    for payment in payments:
        offer = db.query(SparePartOffer).filter(SparePartOffer.id == payment.offer_id).first()
        seller = db.query(Seller).filter(Seller.id == payment.seller_id).first()
        
        payment_dict = {
            "id": payment.id,
            "offer_id": payment.offer_id,
            "user_id": payment.user_id,
            "seller_id": payment.seller_id,
            "amount": payment.amount,
            "total_amount": payment.total_amount,
            "stripe_payment_intent_id": payment.stripe_payment_intent_id,
            "stripe_charge_id": payment.stripe_charge_id,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "offer": {
                "id": offer.id,
                "price": offer.price,
                "description": offer.description,
                "status": offer.status
            } if offer else None,
            "seller": {
                "id": seller.id,
                "business_name": seller.business_name,
                "owner_firstname": seller.owner_firstname,
                "owner_lastname": seller.owner_lastname
            } if seller else None
        }
        result.append(payment_dict)
    
    return result

@app.get("/api/payments/seller-payments", response_model=list[PaymentResponse])
async def get_seller_payments(
    current_seller: Seller = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Get all approved payments for the current seller"""
    payments = db.query(Payment).filter(
        Payment.seller_id == current_seller.id,
        Payment.status == "completed"
    ).order_by(Payment.created_at.desc()).all()
    
    result = []
    for payment in payments:
        offer = db.query(SparePartOffer).filter(SparePartOffer.id == payment.offer_id).first()
        user = db.query(AppUser).filter(AppUser.id == payment.user_id).first()
        
        payment_dict = {
            "id": payment.id,
            "offer_id": payment.offer_id,
            "user_id": payment.user_id,
            "seller_id": payment.seller_id,
            "amount": payment.amount,
            "total_amount": payment.total_amount,
            "stripe_payment_intent_id": payment.stripe_payment_intent_id,
            "stripe_charge_id": payment.stripe_charge_id,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "offer": {
                "id": offer.id,
                "price": offer.price,
                "description": offer.description,
                "status": offer.status
            } if offer else None,
            "user": {
                "id": user.id,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email
            } if user else None
        }
        result.append(payment_dict)
    
    return result

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

@app.get("/admin/transactions")
async def get_all_transactions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payment transactions (Admin only)"""
    query = db.query(Payment)
    
    # Filter by status if provided
    if status:
        query = query.filter(Payment.status == status)
    
    # Get transactions with pagination
    transactions = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for payment in transactions:
        offer = db.query(SparePartOffer).filter(SparePartOffer.id == payment.offer_id).first()
        user = db.query(AppUser).filter(AppUser.id == payment.user_id).first()
        seller = db.query(Seller).filter(Seller.id == payment.seller_id).first()
        
        transaction_dict = {
            "id": payment.id,
            "offer_id": payment.offer_id,
            "user_id": payment.user_id,
            "seller_id": payment.seller_id,
            "amount": payment.amount,
            "total_amount": payment.total_amount,
            "stripe_payment_intent_id": payment.stripe_payment_intent_id,
            "stripe_charge_id": payment.stripe_charge_id,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "offer": {
                "id": offer.id,
                "price": offer.price,
                "description": offer.description,
                "status": offer.status
            } if offer else None,
            "user": {
                "id": user.id,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email
            } if user else None,
            "seller": {
                "id": seller.id,
                "business_name": seller.business_name,
                "owner_firstname": seller.owner_firstname,
                "owner_lastname": seller.owner_lastname
            } if seller else None
        }
        result.append(transaction_dict)
    
    return result

@app.get("/admin/transactions/stats")
async def get_transaction_stats(
    current_admin: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction statistics (Admin only)"""
    from sqlalchemy import func
    
    total_transactions = db.query(func.count(Payment.id)).scalar()
    completed_transactions = db.query(func.count(Payment.id)).filter(
        Payment.status == "completed"
    ).scalar()
    pending_transactions = db.query(func.count(Payment.id)).filter(
        Payment.status == "pending"
    ).scalar()
    failed_transactions = db.query(func.count(Payment.id)).filter(
        Payment.status == "failed"
    ).scalar()
    
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "completed"
    ).scalar() or 0.0
    
    return {
        "total_transactions": total_transactions or 0,
        "completed_transactions": completed_transactions or 0,
        "pending_transactions": pending_transactions or 0,
        "failed_transactions": failed_transactions or 0,
        "total_revenue": float(total_revenue)
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