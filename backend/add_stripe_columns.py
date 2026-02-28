"""
Quick migration script to add stripe_customer_id column and saved_payment_methods table
Run this script to update your database schema
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

def add_stripe_columns():
    with engine.connect() as conn:
        # Add stripe_customer_id to app_users
        print("Adding stripe_customer_id column to app_users table...")
        try:
            conn.execute(text("ALTER TABLE app_users ADD COLUMN stripe_customer_id VARCHAR(255)"))
            conn.commit()
            print("✅ Successfully added stripe_customer_id column to app_users")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate column" in error_msg:
                print("⚠️ stripe_customer_id column already exists in app_users, skipping.")
            else:
                print(f"❌ Error adding stripe_customer_id column: {e}")
                return False

        # Create saved_payment_methods table
        print("\nCreating saved_payment_methods table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS saved_payment_methods (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            stripe_payment_method_id VARCHAR(255) NOT NULL UNIQUE,
            stripe_customer_id VARCHAR(255),
            card_brand VARCHAR(50),
            card_last4 VARCHAR(4),
            card_exp_month INTEGER,
            card_exp_year INTEGER,
            is_default BOOLEAN DEFAULT FALSE,
            created_at VARCHAR,
            updated_at VARCHAR
        )
        """
        # Adjust for SQLite if necessary
        if "sqlite" in DATABASE_URL:
            create_table_sql = create_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        
        try:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ Successfully created saved_payment_methods table")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "already exists" in error_msg:
                print("⚠️ saved_payment_methods table already exists, skipping.")
            else:
                print(f"❌ Error creating saved_payment_methods table: {e}")
                return False

    print("\n✅ Migration completed successfully!")
    return True

if __name__ == "__main__":
    add_stripe_columns()

