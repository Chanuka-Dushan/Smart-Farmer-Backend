import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_base import Base
from models.user import Admin, AppUser

# ==========================================
# Tharushi Inventory Module Models
# These imports are needed so create_all()
# can create missing inventory tables.
# ==========================================

from models.inventory_models import (
    InventorySeason,
    InventoryStage,
    InventoryMachineCategory,
    InventoryBrand,
    InventoryMachineModel,
    InventoryPart,
    InventoryModelPartMapping,
    InventorySeasonalDemandRule,
    InventoryDemandHistory,
    InventoryStockTestRecord,
)

from utils.auth import hash_password

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_farmer.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if not DATABASE_URL.startswith("sqlite") else False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_database():
    """
    Initialize database.

    Important:
    - This will create missing tables only.
    - This will NOT delete existing tables.
    - This will NOT duplicate existing tables.
    - This will NOT add missing columns to existing tables.
    """

    print("🔧 Initializing database...")

    # Create missing tables only
    Base.metadata.create_all(bind=engine)

    print("✓ Missing tables created / existing tables checked")

    db = SessionLocal()

    try:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.email == "admin@farmerlk.me").first()

        if admin:
            print("✓ Admin user already exists")
        else:
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
            print("  Email: admin@farmerlk.me")
            print("  Password: admin@123")
            print("\n⚠️  IMPORTANT: Change the password in production!")

        # Display statistics
        user_count = db.query(AppUser).count()
        admin_count = db.query(Admin).count()

        print("\n📊 Database Statistics:")
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