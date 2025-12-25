import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import Base, Admin, AppUser
from utils.auth import hash_password

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_farmer.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database and create tables"""
    print("🔧 Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.email == "admin@farmerlk.me").first()
        
        if admin:
            print("✓ Admin user already exists")
        else:
            # Create default admin user
            hashed_password = hash_password("admin@123")
            admin = Admin(
                name="Admin",
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
        
        # Display statistics
        user_count = db.query(AppUser).count()
        admin_count = db.query(Admin).count()
        
        print(f"\n📊 Database Statistics:")
        print(f"  Total Admins: {admin_count}")
        print(f"  Total Users: {user_count}")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()
