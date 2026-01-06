"""
DigitalOcean Spaces (S3-compatible) utility functions
"""
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import logging
from typing import BinaryIO, Optional

logger = logging.getLogger(__name__)

# DigitalOcean Spaces configuration
SPACES_REGION = os.getenv("SPACES_REGION", "sfo3")
SPACES_BUCKET = os.getenv("SPACES_BUCKET", "smartfarmer")
SPACES_KEY = os.getenv("SPACES_KEY")
SPACES_SECRET = os.getenv("SPACES_SECRET")
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"
SPACES_CDN_URL = f"https://{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com"

# Initialize S3 client for DigitalOcean Spaces
def get_spaces_client():
    """Get boto3 client configured for DigitalOcean Spaces"""
    if not SPACES_KEY or not SPACES_SECRET:
        logger.warning("Spaces credentials not configured. Uploads will fail.")
        return None
    
    return boto3.client(
        's3',
        region_name=SPACES_REGION,
        endpoint_url=SPACES_ENDPOINT,
        aws_access_key_id=SPACES_KEY,
        aws_secret_access_key=SPACES_SECRET
    )


def upload_file_to_spaces(
    file_obj: BinaryIO,
    object_name: str,
    content_type: str = "image/jpeg",
    folder: str = "spare-parts"
) -> Optional[str]:
    """
    Upload a file to DigitalOcean Spaces
    
    Args:
        file_obj: File object to upload
        object_name: Name for the object in Spaces
        content_type: MIME type of the file
        folder: Folder/prefix in the bucket
    
    Returns:
        str: Public URL of uploaded file or None if failed
    """
    try:
        s3_client = get_spaces_client()
        if not s3_client:
            logger.error("Spaces client not initialized")
            return None
        
        # Construct the full object key with folder
        object_key = f"{folder}/{object_name}"
        
        # Upload file
        s3_client.upload_fileobj(
            file_obj,
            SPACES_BUCKET,
            object_key,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': content_type
            }
        )
        
        # Return public URL
        public_url = f"{SPACES_CDN_URL}/{object_key}"
        logger.info(f"Successfully uploaded to Spaces: {public_url}")
        return public_url
        
    except ClientError as e:
        logger.error(f"Failed to upload to Spaces: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading to Spaces: {str(e)}")
        return None


def delete_file_from_spaces(file_url: str) -> bool:
    """
    Delete a file from DigitalOcean Spaces
    
    Args:
        file_url: Full URL of the file to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        s3_client = get_spaces_client()
        if not s3_client:
            return False
        
        # Extract object key from URL
        # URL format: https://smartfarmer.sfo3.digitaloceanspaces.com/spare-parts/filename.jpg
        if SPACES_CDN_URL in file_url:
            object_key = file_url.replace(f"{SPACES_CDN_URL}/", "")
        else:
            logger.warning(f"Invalid Spaces URL format: {file_url}")
            return False
        
        # Delete object
        s3_client.delete_object(Bucket=SPACES_BUCKET, Key=object_key)
        logger.info(f"Successfully deleted from Spaces: {object_key}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to delete from Spaces: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting from Spaces: {str(e)}")
        return False


def generate_unique_filename(user_id: int, original_filename: str) -> str:
    """
    Generate a unique filename for upload
    
    Args:
        user_id: ID of the user uploading
        original_filename: Original name of the file
    
    Returns:
        str: Unique filename
    """
    file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
    timestamp = datetime.now(timezone.utc).timestamp()
    return f"{user_id}_{timestamp}.{file_extension}"


def is_spaces_configured() -> bool:
    """Check if Spaces credentials are configured"""
    return bool(SPACES_KEY and SPACES_SECRET)


def get_content_type(filename: str) -> str:
    """Get content type from filename"""
    extension = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }
    
    return content_types.get(extension, 'application/octet-stream')
