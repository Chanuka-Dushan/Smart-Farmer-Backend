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

def fix_image_paths():
    with engine.connect() as conn:
        print("Fixing image paths in spare_part_requests table...")
        
        # Get all requests with image URLs
        result = conn.execute(text("SELECT id, image_url FROM spare_part_requests WHERE image_url IS NOT NULL"))
        requests = result.fetchall()
        
        fixed_count = 0
        for req_id, image_url in requests:
            if image_url and not image_url.startswith('/uploads/'):
                # Fix paths like /spare_parts/ or /spare-parts/
                new_url = image_url
                if '/spare_parts/' in image_url:
                    new_url = image_url.replace('/spare_parts/', '/uploads/spare-parts/')
                elif '/spare-parts/' in image_url:
                    new_url = image_url.replace('/spare-parts/', '/uploads/spare-parts/')
                
                if new_url != image_url:
                    print(f"Fixing ID {req_id}: {image_url} -> {new_url}")
                    conn.execute(text("UPDATE spare_part_requests SET image_url = :new_url WHERE id = :id"), 
                               {"new_url": new_url, "id": req_id})
                    fixed_count += 1
        
        conn.commit()
        print(f"Fixed {fixed_count} image paths")

if __name__ == "__main__":
    fix_image_paths()
    print("Fix completed!")
