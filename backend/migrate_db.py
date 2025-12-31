import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate():
    with engine.connect() as conn:
        # --- 1. Migrate app_users table ---
        print("Checking/Adding columns to app_users table...")
        app_user_columns = [
            ("profile_picture_url", "VARCHAR(500)"),
            ("google_id", "VARCHAR(255)"),
            ("facebook_id", "VARCHAR(255)"),
            ("is_social_login", "BOOLEAN DEFAULT FALSE"),
            ("is_deleted", "BOOLEAN DEFAULT FALSE"),
            ("is_banned", "BOOLEAN DEFAULT FALSE")
        ]

        for col_name, col_type in app_user_columns:
            try:
                conn.execute(text(f"ALTER TABLE app_users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Successfully added column to app_users: {col_name}")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate column" in error_msg:
                    print(f"Column {col_name} in app_users already exists, skipping.")
                else:
                    print(f"Error adding {col_name} to app_users: {e}")

        # --- 2. Migrate sellers table ---
        print("\nChecking/Adding columns to sellers table...")
        seller_columns = [
            ("logo_url", "VARCHAR(500)"),
            ("onboarding_completed", "BOOLEAN DEFAULT FALSE"),
            ("fcm_token", "VARCHAR(500)"),
            ("google_id", "VARCHAR(255)"),
            ("facebook_id", "VARCHAR(255)"),
            ("is_social_login", "BOOLEAN DEFAULT FALSE")
        ]

        for col_name, col_type in seller_columns:
            try:
                conn.execute(text(f"ALTER TABLE sellers ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Successfully added column to sellers: {col_name}")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate column" in error_msg:
                    print(f"Column {col_name} in sellers already exists, skipping.")
                else:
                    print(f"Error adding {col_name} to sellers: {e}")

        # --- 3. Ensure password_resets table exists ---
        print("\nChecking/Creating password_resets table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS password_resets (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        # Adjust for SQLite if necessary
        if "sqlite" in DATABASE_URL:
            create_table_sql = create_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            create_table_sql = create_table_sql.replace("TIMESTAMP", "DATETIME")

        try:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("Successfully ensured password_resets table exists.")
        except Exception as e:
            print(f"Error creating password_resets table: {e}")

    print("\nMigration process finished.")

if __name__ == "__main__":
    migrate()
