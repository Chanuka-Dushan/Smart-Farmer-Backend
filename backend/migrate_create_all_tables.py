"""
Migration script to create all missing tables in PostgreSQL
Run this once after deploying to Digital Ocean
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models to register them with Base
from models.user import Base as UserBase
from models.identification import Base as IdentBase, IdentificationPart, IdentificationTractor, IdentificationPartCompatibility
from models.part import Base as PartBase, Part
from db_base import Base

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_farmer.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_all_tables():
    """Create all tables from all Base instances"""
    print("🔧 Creating all database tables...")
    print(f"📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    try:
        # Get inspector to see existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"\n📋 Existing tables: {existing_tables if existing_tables else 'None'}\n")
        
        # Create all tables from all Base instances
        Base.metadata.create_all(bind=engine)
        UserBase.metadata.create_all(bind=engine)
        IdentBase.metadata.create_all(bind=engine)
        PartBase.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        current_tables = inspector.get_table_names()
        
        print("✅ Created tables:")
        for table in current_tables:
            columns = [col['name'] for col in inspector.get_columns(table)]
            print(f"   ✓ {table}")
            print(f"     Columns: {', '.join(columns)}")
        
        print(f"\n✅ Total tables: {len(current_tables)}")
        print("✅ All tables created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_all_tables()
