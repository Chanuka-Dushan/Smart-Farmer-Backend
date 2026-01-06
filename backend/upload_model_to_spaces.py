"""
Upload ML model to DigitalOcean Spaces
Run this script once to upload your trained model
"""
import os
import boto3
from botocore.client import Config
from pathlib import Path

# DigitalOcean Spaces Configuration
SPACES_KEY = os.getenv('SPACES_KEY', 'YOUR_SPACES_KEY')
SPACES_SECRET = os.getenv('SPACES_SECRET', 'YOUR_SPACES_SECRET')
SPACES_REGION = os.getenv('SPACES_REGION', 'nyc3')
SPACES_BUCKET = os.getenv('SPACES_BUCKET', 'YOUR_BUCKET_NAME')

# Model file
MODEL_FILE = 'smart_farmer_vision_v1.h5'
MODEL_PATH = Path(__file__).parent / MODEL_FILE

def upload_model_to_spaces():
    """Upload the ML model to DigitalOcean Spaces"""
    
    if not MODEL_PATH.exists():
        print(f"❌ Model file not found: {MODEL_PATH}")
        return False
    
    print(f"📦 Uploading {MODEL_FILE} to DigitalOcean Spaces...")
    print(f"   File size: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Create Spaces client
        session = boto3.session.Session()
        client = session.client('s3',
            region_name=SPACES_REGION,
            endpoint_url=f'https://{SPACES_REGION}.digitaloceanspaces.com',
            aws_access_key_id=SPACES_KEY,
            aws_secret_access_key=SPACES_SECRET,
            config=Config(signature_version='s3v4')
        )
        
        # Upload model
        print(f"📤 Uploading to: {SPACES_BUCKET}/models/{MODEL_FILE}")
        client.upload_file(
            str(MODEL_PATH),
            SPACES_BUCKET,
            f'models/{MODEL_FILE}',
            ExtraArgs={'ACL': 'private'}
        )
        
        print(f"✅ Model uploaded successfully!")
        print(f"   URL: https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/models/{MODEL_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("UPLOAD ML MODEL TO DIGITALOCEAN SPACES")
    print("=" * 60)
    print()
    
    # Check environment variables
    if SPACES_KEY == 'YOUR_SPACES_KEY':
        print("⚠️  Please set your DigitalOcean Spaces credentials:")
        print("   export SPACES_KEY=your_key")
        print("   export SPACES_SECRET=your_secret")
        print("   export SPACES_BUCKET=your_bucket_name")
        print()
        print("Or edit this script and replace the placeholders")
        exit(1)
    
    success = upload_model_to_spaces()
    
    if success:
        print()
        print("=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Add this environment variable in DigitalOcean:")
        print(f"   MODEL_URL=https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/models/{MODEL_FILE}")
        print()
        print("2. The app will automatically download the model on startup")
        print()
        print("3. Redeploy your app")
    else:
        exit(1)
