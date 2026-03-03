"""
Migration script to add payments table
Run this script to create the payments table in your database
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")

engine = create_engine(DATABASE_URL)

def create_payments_table():
    with engine.connect() as conn:
        # Create payments table
        print("Creating payments table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            stripe_payment_intent_id VARCHAR(255),
            stripe_charge_id VARCHAR(255),
            status VARCHAR(50) DEFAULT 'pending',
            payment_method VARCHAR(50) DEFAULT 'stripe',
            created_at VARCHAR,
            updated_at VARCHAR
        )
        """
        # Adjust for PostgreSQL if necessary
        if "postgresql" in DATABASE_URL:
            create_table_sql = create_table_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

        try:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("Successfully created payments table")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "already exists" in error_msg:
                print("payments table already exists, skipping.")
            else:
                print(f"Error creating payments table: {e}")
                return False

    print("\nMigration completed successfully!")
    return True

if __name__ == "__main__":
    create_payments_table()
