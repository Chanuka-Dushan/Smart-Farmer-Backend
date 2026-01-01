from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AppUser(Base):
    """
    Mobile App User Model
    This represents users who use the mobile application
    """
    __tablename__ = "app_users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    fcm_token = Column(String(500), nullable=True)  # For push notifications
    address = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Seller(Base):
    """
    Seller Model
    This represents sellers who can sell products through the platform
    """
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
    shop_location_name = Column(String(255), nullable=True)  # e.g., "Main Market", "Downtown Branch"
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    fcm_token = Column(String(500), nullable=True)  # For push notifications
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    """
    Notification Model
    This represents notifications sent to users
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    user_type = Column(String(50), nullable=False)  # 'app_user', 'seller', 'all'
    target_user_id = Column(Integer, nullable=True)  # Specific user ID, null for broadcast
    sent_by = Column(Integer, nullable=False)  # Admin ID who sent the notification
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    """
    Admin User Model
    This represents administrators who access the dashboard
    """
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
