"""
Migration script to add created_at and updated_at columns to admins table
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_farmer.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def migrate_add_timestamps():
    """Add created_at and updated_at columns to admins table"""
    print("🔄 Running migration: Add timestamps to admins table...")
    
    with engine.connect() as connection:
        try:
            # Check if columns already exist
            if "sqlite" in DATABASE_URL:
                # SQLite - check schema
                result = connection.execute(text("PRAGMA table_info(admins)"))
                columns = [row[1] for row in result]
                
                if "created_at" not in columns:
                    print("  ➕ Adding created_at column...")
                    connection.execute(text("""
                        ALTER TABLE admins 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    connection.commit()
                
                if "updated_at" not in columns:
                    print("  ➕ Adding updated_at column...")
                    connection.execute(text("""
                        ALTER TABLE admins 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    connection.commit()
            else:
                # PostgreSQL - check information_schema
                result = connection.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='admins'
                """))
                columns = [row[0] for row in result]
                
                if "created_at" not in columns:
                    print("  ➕ Adding created_at column...")
                    connection.execute(text("""
                        ALTER TABLE admins 
                        ADD COLUMN created_at TIMESTAMP DEFAULT NOW()
                    """))
                    connection.commit()
                
                if "updated_at" not in columns:
                    print("  ➕ Adding updated_at column...")
                    connection.execute(text("""
                        ALTER TABLE admins 
                        ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
                    """))
                    connection.commit()
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            connection.rollback()
            raise

if __name__ == "__main__":
    migrate_add_timestamps()
