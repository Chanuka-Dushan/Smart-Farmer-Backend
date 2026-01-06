"""
Migration script to fix spare parts image paths and move files to correct directory
This script:
1. Creates the spare-parts directory if it doesn't exist
2. Fixes image paths in the database 
3. Moves any misplaced image files to the correct location
"""
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_engine(DATABASE_URL)

def fix_image_paths_and_files():
    # Create the correct directory structure
    upload_dir = Path("uploads/spare-parts")
    upload_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created/verified directory: {upload_dir}")
    
    # Check for old directories that might have files
    old_dirs = [
        Path("uploads/spare_parts"),
        Path("spare_parts"),
        Path("spare-parts")
    ]
    
    # Move files from old directories to new directory
    moved_files = 0
    for old_dir in old_dirs:
        if old_dir.exists() and old_dir.is_dir():
            print(f"\nFound old directory: {old_dir}")
            for file in old_dir.glob("*.jpg"):
                new_path = upload_dir / file.name
                if not new_path.exists():
                    shutil.move(str(file), str(new_path))
                    print(f"  Moved: {file.name}")
                    moved_files += 1
                else:
                    print(f"  Skipped (exists): {file.name}")
    
    print(f"\n✓ Moved {moved_files} files to correct directory")
    
    # Fix database paths
    with engine.connect() as conn:
        print("\nFixing image paths in database...")
        
        # Get all requests with image URLs
        result = conn.execute(text("SELECT id, image_url FROM spare_part_requests WHERE image_url IS NOT NULL"))
        requests = result.fetchall()
        
        fixed_count = 0
        for req_id, image_url in requests:
            if image_url:
                old_url = image_url
                new_url = image_url
                
                # Fix various incorrect path formats
                if '/spare_parts/' in image_url:
                    new_url = image_url.replace('/spare_parts/', '/uploads/spare-parts/')
                elif image_url.startswith('/uploads/spare_parts/'):
                    new_url = image_url.replace('/uploads/spare_parts/', '/uploads/spare-parts/')
                elif image_url.startswith('/spare-parts/'):
                    new_url = '/uploads' + image_url
                elif not image_url.startswith('/uploads/'):
                    # Add /uploads/spare-parts/ prefix if missing
                    filename = os.path.basename(image_url)
                    new_url = f'/uploads/spare-parts/{filename}'
                
                if new_url != old_url:
                    print(f"  ID {req_id}: {old_url} -> {new_url}")
                    conn.execute(
                        text("UPDATE spare_part_requests SET image_url = :new_url WHERE id = :id"), 
                        {"new_url": new_url, "id": req_id}
                    )
                    fixed_count += 1
        
        conn.commit()
        print(f"\n✓ Fixed {fixed_count} image path(s) in database")
    
    # List files in the correct directory
    files_in_correct_dir = list(upload_dir.glob("*.jpg"))
    print(f"\n✓ Current files in {upload_dir}: {len(files_in_correct_dir)}")
    if files_in_correct_dir and len(files_in_correct_dir) <= 10:
        for f in files_in_correct_dir:
            print(f"  - {f.name}")

if __name__ == "__main__":
    try:
        fix_image_paths_and_files()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
