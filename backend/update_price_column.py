import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_engine(DATABASE_URL)

def update_price_column():
    with engine.connect() as conn:
        print("Updating spare_part_offers price column to REAL/FLOAT...")
        try:
            # For SQLite
            if 'sqlite' in DATABASE_URL:
                # SQLite doesn't support ALTER COLUMN, need to recreate table
                print("SQLite detected - recreating table with new schema...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS spare_part_offers_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id INTEGER NOT NULL,
                        seller_id INTEGER NOT NULL,
                        price REAL NOT NULL,
                        description TEXT NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at VARCHAR,
                        updated_at VARCHAR
                    )
                """))
                
                # Copy data, converting price to float
                conn.execute(text("""
                    INSERT INTO spare_part_offers_new 
                    SELECT id, request_id, seller_id, 
                           CAST(price AS REAL), 
                           description, status, created_at, updated_at
                    FROM spare_part_offers
                """))
                
                # Drop old table and rename new one
                conn.execute(text("DROP TABLE spare_part_offers"))
                conn.execute(text("ALTER TABLE spare_part_offers_new RENAME TO spare_part_offers"))
                
                conn.commit()
                print("Successfully updated price column to REAL")
            else:
                # For PostgreSQL
                conn.execute(text("ALTER TABLE spare_part_offers ALTER COLUMN price TYPE REAL USING price::real"))
                conn.commit()
                print("Successfully updated price column to REAL")
        except Exception as e:
            conn.rollback()
            print(f"Error updating price column: {e}")

if __name__ == "__main__":
    update_price_column()
    print("Update completed!")
