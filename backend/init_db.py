import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from utils.database import engine
from db_base import Base

# Load environment
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./admin.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Import models
from main import Base, User

def create_admin_user():
    """Create admin user in database"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@farmerlk.me").first()
        
        if admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        hashed_password = pwd_context.hash("admin@123")
        admin = User(
            email="admin@farmerlk.me",
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✓ Admin user created successfully")
        print(f"  Email: admin@farmerlk.me")
        print(f"  Password: admin@123")
        print("\n⚠️  IMPORTANT: Change the password in production!")
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
