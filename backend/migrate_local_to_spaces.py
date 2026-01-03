"""
Migrate local images to DigitalOcean Spaces
This script uploads all local images to Spaces and updates database paths
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Import Spaces utilities
sys.path.insert(0, os.path.dirname(__file__))
from spaces_utils import (
    get_spaces_client,
    SPACES_BUCKET,
    SPACES_CDN_URL,
    is_spaces_configured
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


def migrate_images_to_spaces():
    """Migrate all local images to DigitalOcean Spaces"""
    
    if not is_spaces_configured():
        print("❌ Spaces not configured. Please set SPACES_KEY and SPACES_SECRET")
        return False
    
    s3_client = get_spaces_client()
    if not s3_client:
        print("❌ Failed to initialize Spaces client")
        return False
    
    print("✓ Spaces client initialized")
    print(f"✓ Bucket: {SPACES_BUCKET}")
    print(f"✓ CDN URL: {SPACES_CDN_URL}\n")
    
    # Find local images
    local_dirs = [
        Path("uploads/spare-parts"),
        Path("uploads/spare_parts"),
        Path("spare-parts"),
        Path("spare_parts")
    ]
    
    uploaded_files = []
    failed_files = []
    
    for local_dir in local_dirs:
        if not local_dir.exists():
            continue
        
        print(f"📁 Scanning: {local_dir}")
        
        for image_file in local_dir.glob("*.jpg"):
            try:
                # Upload to Spaces
                object_key = f"spare-parts/{image_file.name}"
                
                with open(image_file, 'rb') as f:
                    s3_client.upload_fileobj(
                        f,
                        SPACES_BUCKET,
                        object_key,
                        ExtraArgs={
                            'ACL': 'public-read',
                            'ContentType': 'image/jpeg'
                        }
                    )
                
                new_url = f"{SPACES_CDN_URL}/{object_key}"
                uploaded_files.append((image_file.name, new_url))
                print(f"  ✓ Uploaded: {image_file.name}")
                
            except ClientError as e:
                failed_files.append((image_file.name, str(e)))
                print(f"  ❌ Failed: {image_file.name} - {str(e)}")
            except Exception as e:
                failed_files.append((image_file.name, str(e)))
                print(f"  ❌ Error: {image_file.name} - {str(e)}")
    
    print(f"\n📊 Upload Summary:")
    print(f"  ✓ Uploaded: {len(uploaded_files)}")
    print(f"  ❌ Failed: {len(failed_files)}")
    
    if failed_files:
        print("\n❌ Failed files:")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    # Update database paths
    if uploaded_files:
        print("\n🔄 Updating database paths...")
        update_database_paths(uploaded_files)
    
    return len(failed_files) == 0


def update_database_paths(uploaded_files):
    """Update database to point to Spaces URLs"""
    with engine.connect() as conn:
        updated_count = 0
        
        for filename, new_url in uploaded_files:
            # Find records with this filename in various path formats
            patterns = [
                f'/uploads/spare-parts/{filename}',
                f'/uploads/spare_parts/{filename}',
                f'/spare-parts/{filename}',
                f'/spare_parts/{filename}',
                filename
            ]
            
            for pattern in patterns:
                result = conn.execute(
                    text(
                        "UPDATE spare_part_requests SET image_url = :new_url "
                        "WHERE image_url LIKE :pattern"
                    ),
                    {"new_url": new_url, "pattern": f"%{pattern}%"}
                )
                if result.rowcount > 0:
                    updated_count += result.rowcount
                    print(f"  ✓ Updated {result.rowcount} record(s) for: {filename}")
        
        conn.commit()
        print(f"\n✓ Updated {updated_count} database record(s)")


def verify_spaces_access():
    """Verify we can access the Spaces bucket"""
    try:
        s3_client = get_spaces_client()
        if not s3_client:
            return False
        
        # Try to list objects (limited to 1)
        response = s3_client.list_objects_v2(Bucket=SPACES_BUCKET, MaxKeys=1)
        print(f"✓ Bucket accessible: {SPACES_BUCKET}")
        return True
        
    except ClientError as e:
        print(f"❌ Cannot access bucket: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Farmer - Migrate Local Images to DigitalOcean Spaces")
    print("=" * 60)
    print()
    
    # Verify Spaces access
    print("🔍 Verifying Spaces access...")
    if not verify_spaces_access():
        print("\n❌ Cannot proceed without Spaces access")
        sys.exit(1)
    
    print()
    
    # Confirm before proceeding
    response = input("Continue with migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled")
        sys.exit(0)
    
    print()
    
    # Run migration
    success = migrate_images_to_spaces()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Test image uploads through the app")
        print("  2. Verify images load correctly")
        print("  3. Remove local uploads volume from docker-compose.yml")
        print("  4. Redeploy the application")
    else:
        print("\n⚠ Migration completed with errors")
        print("Please review failed files and try again")
