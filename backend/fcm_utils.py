"""
Enhanced Firebase Cloud Messaging (FCM) Utility using Firebase Admin SDK
Send push notifications to mobile app users with comprehensive error handling and logging
"""

import os
import logging
import json
import time
from typing import Optional, Dict, List, Union, Tuple
from dotenv import load_dotenv

# Firebase Admin SDK imports
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False
    logging.warning("Firebase Admin SDK not installed. Please install: pip install firebase-admin")

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_ADMIN_SDK_PATH = os.getenv("FIREBASE_ADMIN_SDK_PATH", "")

# Alternative: Environment variables for service account
FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n')
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID", "")
FIREBASE_AUTH_URI = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
FIREBASE_TOKEN_URI = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")

# Initialize Firebase Admin SDK
_firebase_app = None


def initialize_firebase_admin():
    """Initialize Firebase Admin SDK with service account credentials"""
    global _firebase_app
    
    if not FIREBASE_ADMIN_AVAILABLE:
        logger.error("Firebase Admin SDK is not installed")
        return False
    
    if _firebase_app:
        return True
        
    try:
        # Check if already initialized with our custom name
        try:
            _firebase_app = firebase_admin.get_app('smart_farmer_app')
            logger.info("Firebase Admin SDK already initialized (smart_farmer_app)")
            return True
        except ValueError:
            # Try default app
            try:
                _firebase_app = firebase_admin.get_app()
                logger.info("Firebase Admin SDK already initialized (default)")
                return True
            except ValueError:
                # Not initialized, proceed with initialization
                pass
    except Exception as e:
        logger.warning(f"Error checking Firebase app: {e}")
        # Continue with initialization
        pass
    
    try:
        cred = None
        
        # Method 1: Use service account file
        if FIREBASE_ADMIN_SDK_PATH and os.path.exists(FIREBASE_ADMIN_SDK_PATH):
            try:
                cred = credentials.Certificate(FIREBASE_ADMIN_SDK_PATH)
                logger.info(f"Using Firebase Admin SDK file: {FIREBASE_ADMIN_SDK_PATH}")
            except Exception as e:
                logger.error(f"Failed to load credentials from file: {e}")
                return False
            
        # Method 2: Use environment variables
        elif all([FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL, FIREBASE_CLIENT_ID]):
            try:
                service_account_info = {
                    "type": "service_account",
                    "project_id": FIREBASE_PROJECT_ID,
                    "private_key_id": FIREBASE_PRIVATE_KEY_ID,
                    "private_key": FIREBASE_PRIVATE_KEY,
                    "client_email": FIREBASE_CLIENT_EMAIL,
                    "client_id": FIREBASE_CLIENT_ID,
                    "auth_uri": FIREBASE_AUTH_URI,
                    "token_uri": FIREBASE_TOKEN_URI,
                }
                cred = credentials.Certificate(service_account_info)
                logger.info("Using Firebase Admin SDK from environment variables")
            except Exception as e:
                logger.error(f"Failed to create credentials from environment variables: {e}")
                return False
            
        else:
            logger.error("No valid Firebase credentials found. Please set up either:")
            logger.error("1. FIREBASE_ADMIN_SDK_PATH pointing to service account JSON file")
            logger.error("2. Environment variables: FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY, etc.")
            return False
        
        # Validate project ID
        if not FIREBASE_PROJECT_ID or not FIREBASE_PROJECT_ID.strip():
            logger.error("FIREBASE_PROJECT_ID is required but not set")
            return False
        
        # Initialize the app with explicit project ID
        try:
            _firebase_app = firebase_admin.initialize_app(
                cred, 
                {
                    'projectId': FIREBASE_PROJECT_ID.strip(),
                },
                name='smart_farmer_app'  # Use a unique name to avoid conflicts
            )
            logger.info(f"Firebase Admin SDK initialized successfully for project: {FIREBASE_PROJECT_ID}")
            return True
        except ValueError as e:
            # App might already be initialized
            if "already exists" in str(e).lower():
                logger.info("Firebase Admin SDK already initialized")
                try:
                    _firebase_app = firebase_admin.get_app('smart_farmer_app')
                except ValueError:
                    _firebase_app = firebase_admin.get_app()
                return True
            else:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
                return False
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        return False


class FCMError(Exception):
    """Custom exception for FCM errors"""
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


def validate_fcm_config() -> bool:
    """Validate FCM configuration"""
    if not FIREBASE_ADMIN_AVAILABLE:
        logger.error("Firebase Admin SDK not available. Please install: pip install firebase-admin")
        return False
        
    if not FIREBASE_PROJECT_ID or not FIREBASE_PROJECT_ID.strip():
        logger.error("Firebase Project ID not configured. Please set FIREBASE_PROJECT_ID in environment")
        return False
    
    # Initialize Firebase Admin SDK
    initialized = initialize_firebase_admin()
    if not initialized:
        logger.error("Firebase Admin SDK initialization failed. Check your credentials.")
        return False
    
    # Verify the app is properly initialized - try multiple app names
    try:
        app = None
        # Try to get the app with our custom name first
        try:
            app = firebase_admin.get_app('smart_farmer_app')
        except ValueError:
            # Try default app
            try:
                app = firebase_admin.get_app()
            except ValueError:
                # App doesn't exist, try to initialize again
                logger.warning("Firebase app not found, attempting to re-initialize...")
                if initialize_firebase_admin():
                    try:
                        app = firebase_admin.get_app('smart_farmer_app')
                    except ValueError:
                        app = firebase_admin.get_app()
                else:
                    raise ValueError("Failed to initialize Firebase app")
        
        if app:
            if hasattr(app, 'project_id') and app.project_id != FIREBASE_PROJECT_ID.strip():
                logger.warning(f"Firebase app project ID ({app.project_id}) doesn't match configured project ID ({FIREBASE_PROJECT_ID})")
            logger.info("Firebase app verified successfully")
            return True
        else:
            logger.error("Firebase app is None after initialization")
            return False
            
    except ValueError as e:
        if "does not exist" in str(e):
            logger.error("Firebase app does not exist. Attempting to initialize...")
            if initialize_firebase_admin():
                return True
        logger.error(f"Failed to verify Firebase app: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase app: {e}")
        return False


def send_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = "high",
    sound: str = "default",
    badge: Optional[int] = None,
    click_action: Optional[str] = None,
    timeout: int = 30
) -> Tuple[bool, Dict]:
    """
    Send a push notification to a single device using Firebase Admin SDK
    
    Args:
        fcm_token: The FCM token of the target device
        title: Notification title
        body: Notification body/message
        data: Optional custom data payload
        priority: Notification priority ('high' or 'normal')
        sound: Notification sound ('default' or 'none')
        badge: Badge count for iOS
        click_action: Action when notification is clicked
        timeout: Request timeout in seconds (not used with Admin SDK)
    
    Returns:
        Tuple of (success: bool, response: Dict)
    """
    
    if not validate_fcm_config():
        return False, {"error": "FCM not properly configured"}
    
    if not fcm_token or not fcm_token.strip():
        logger.error("Empty FCM token provided")
        return False, {"error": "Invalid FCM token"}
    
    if not title or not body:
        logger.error("Title and body are required")
        return False, {"error": "Title and body are required"}
    
    try:
        # Build the message
        android_config = messaging.AndroidConfig(
            priority=priority,
            notification=messaging.AndroidNotification(
                title=title,
                body=body,
                sound=sound,
                channel_id='smart_farmer_channel',
                default_sound=True,
                click_action=click_action or 'FLUTTER_NOTIFICATION_CLICK'
            )
        )
        
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound=sound,
                    badge=badge,
                    content_available=True
                )
            )
        )
        
        # Convert data values to strings (required by FCM)
        string_data = {}
        if data:
            string_data = {k: str(v) for k, v in data.items()}
        
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=string_data,
            token=fcm_token.strip(),
            android=android_config,
            apns=apns_config
        )
        
        logger.info(f"Sending notification to token: {fcm_token[:10]}...")
        
        # Send the message
        response = messaging.send(message)
        
        logger.info(f"Notification sent successfully. Message ID: {response}")
        return True, {"success": True, "message_id": response}
        
    except messaging.UnregisteredError:
        error_msg = "FCM token is no longer valid (unregistered)"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "unregistered"}
        
    except messaging.SenderIdMismatchError:
        error_msg = "FCM sender ID mismatch"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "sender_mismatch"}
        
    except messaging.QuotaExceededError:
        error_msg = "FCM quota exceeded"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "quota_exceeded"}
        
    except messaging.UnavailableError:
        error_msg = "FCM service temporarily unavailable"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "unavailable"}
        
    except messaging.InvalidArgumentError as e:
        error_msg = f"Invalid FCM argument: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "invalid_argument"}
        
    except Exception as e:
        error_msg = f"Unexpected FCM error: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg, "error_type": "unknown"}


def send_multicast_notification(
    fcm_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = "high",
    sound: str = "default",
    badge: Optional[int] = None,
    batch_size: int = 500
) -> Dict:
    """
    Send push notifications to multiple devices using Firebase Admin SDK batch processing
    
    Args:
        fcm_tokens: List of FCM tokens
        title: Notification title
        body: Notification body
        data: Optional custom data payload
        priority: Notification priority ('high' or 'normal')
        sound: Notification sound
        badge: Badge count for iOS
        batch_size: Number of tokens to process per batch (max 500 for Admin SDK)
    
    Returns:
        Dict with success/failure statistics and details
    """
    
    if not validate_fcm_config():
        return {"success": False, "error": "FCM not properly configured"}
    
    if not fcm_tokens:
        logger.error("No FCM tokens provided")
        return {"success": False, "error": "No tokens provided"}
    
    if not title or not body:
        logger.error("Title and body are required")
        return {"success": False, "error": "Title and body are required"}
    
    # Remove invalid tokens
    valid_tokens = [token.strip() for token in fcm_tokens if token and token.strip()]
    
    if not valid_tokens:
        logger.error("No valid FCM tokens found")
        return {"success": False, "error": "No valid tokens found"}
    
    # Split tokens into batches (Admin SDK supports up to 500 tokens per batch)
    batches = [valid_tokens[i:i + batch_size] for i in range(0, len(valid_tokens), batch_size)]
    
    total_success = 0
    total_failure = 0
    failed_tokens = []
    invalid_tokens = []
    
    try:
        # Build the message template
        android_config = messaging.AndroidConfig(
            priority=priority,
            notification=messaging.AndroidNotification(
                title=title,
                body=body,
                sound=sound,
                channel_id='smart_farmer_channel',
                default_sound=True
            )
        )
        
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound=sound,
                    badge=badge,
                    content_available=True
                )
            )
        )
        
        # Convert data values to strings
        string_data = {}
        if data:
            string_data = {k: str(v) for k, v in data.items()}
        
        for batch_index, batch_tokens in enumerate(batches):
            logger.info(f"Processing batch {batch_index + 1}/{len(batches)} with {len(batch_tokens)} tokens")
            
            try:
                # Create multicast message
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(title=title, body=body),
                    data=string_data,
                    tokens=batch_tokens,
                    android=android_config,
                    apns=apns_config
                )
                
                # Send the batch with error handling
                try:
                    # Ensure we're using the correct Firebase app
                    app = None
                    try:
                        app = firebase_admin.get_app('smart_farmer_app')
                    except ValueError:
                        try:
                            app = firebase_admin.get_app()
                        except ValueError:
                            pass
                    
                    if app:
                        response = messaging.send_multicast(message, app=app)
                    else:
                        response = messaging.send_multicast(message)
                        
                except Exception as send_error:
                    error_str = str(send_error)
                    # Check if it's the 404 batch error
                    if '404' in error_str or '/batch' in error_str or 'not found' in error_str.lower():
                        logger.warning(f"Batch endpoint error detected, falling back to individual sends: {send_error}")
                        # If batch send fails due to endpoint issue, try sending individually
                        for token in batch_tokens:
                            try:
                                individual_message = messaging.Message(
                                    notification=messaging.Notification(title=title, body=body),
                                    data=string_data,
                                    token=token,
                                    android=android_config,
                                    apns=apns_config
                                )
                                if app:
                                    messaging.send(individual_message, app=app)
                                else:
                                    messaging.send(individual_message)
                                total_success += 1
                            except messaging.UnregisteredError:
                                invalid_tokens.append(token)
                                total_failure += 1
                            except Exception as e:
                                failed_tokens.append(token)
                                total_failure += 1
                                logger.error(f"Failed to send to {token[:10]}...: {e}")
                        continue
                    else:
                        # Re-raise if it's a different error
                        raise
                
                total_success += response.success_count
                total_failure += response.failure_count
                
                # Process individual responses
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        token = batch_tokens[idx]
                        error = resp.exception
                        
                        if isinstance(error, messaging.UnregisteredError):
                            invalid_tokens.append(token)
                            logger.warning(f"Token {token[:10]}... is unregistered")
                        else:
                            failed_tokens.append(token)
                            logger.error(f"Failed to send to {token[:10]}...: {error}")
            
            except Exception as batch_error:
                error_msg = f"Error processing batch {batch_index + 1}: {str(batch_error)}"
                logger.error(error_msg)
                # Continue with next batch instead of failing completely
                total_failure += len(batch_tokens)
                failed_tokens.extend(batch_tokens)
                continue
            
            # Small delay between batches to avoid rate limiting
            if batch_index < len(batches) - 1:
                time.sleep(0.1)
    
    except Exception as e:
        error_msg = f"Batch notification error: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": error_msg}
    
    result = {
        "success": True,
        "total_sent": len(valid_tokens),
        "successful": total_success,
        "failed": total_failure,
        "invalid_tokens_count": len(invalid_tokens),
        "failed_tokens_count": len(failed_tokens),
    }
    
    logger.info(f"Batch notification completed: {total_success} successful, {total_failure} failed")
    
    return result


def send_notification_to_topic(
    topic: str,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = "high",
    sound: str = "default",
    badge: Optional[int] = None
) -> Tuple[bool, Dict]:
    """
    Send a notification to a Firebase topic using Firebase Admin SDK
    
    Args:
        topic: Firebase topic name
        title: Notification title
        body: Notification body
        data: Optional custom data payload
        priority: Notification priority
        sound: Notification sound
        badge: Badge count for iOS
    
    Returns:
        Tuple of (success: bool, response: Dict)
    """
    
    if not validate_fcm_config():
        return False, {"error": "FCM not properly configured"}
    
    if not topic or not topic.strip():
        logger.error("Empty topic provided")
        return False, {"error": "Invalid topic"}
    
    if not title or not body:
        logger.error("Title and body are required")
        return False, {"error": "Title and body are required"}
    
    try:
        # Build the message
        android_config = messaging.AndroidConfig(
            priority=priority,
            notification=messaging.AndroidNotification(
                title=title,
                body=body,
                sound=sound,
                channel_id='smart_farmer_channel',
                default_sound=True
            )
        )
        
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound=sound,
                    badge=badge,
                    content_available=True
                )
            )
        )
        
        # Convert data values to strings
        string_data = {}
        if data:
            string_data = {k: str(v) for k, v in data.items()}
        
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=string_data,
            topic=topic.strip(),
            android=android_config,
            apns=apns_config
        )
        
        logger.info(f"Sending notification to topic: {topic}")
        
        # Send the message
        response = messaging.send(message)
        
        logger.info(f"Topic notification sent successfully. Message ID: {response}")
        return True, {"success": True, "message_id": response}
        
    except Exception as e:
        error_msg = f"Topic notification error: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg}


class NotificationTemplates:
    """Pre-defined notification templates for different scenarios"""
    
    @staticmethod
    def welcome_notification(user_name: str) -> Dict:
        return {
            "title": "Welcome to Smart Farmer! 🌱",
            "body": f"Hello {user_name}! Start your farming journey with us.",
            "data": {"type": "welcome", "user_name": user_name}
        }
    
    @staticmethod
    def weather_alert(weather_type: str, temperature: float, location: str) -> Dict:
        return {
            "title": f"Weather Alert: {weather_type} 🌦️",
            "body": f"Current temperature is {temperature}°C in {location}",
            "data": {"type": "weather", "weather_type": weather_type, "temperature": str(temperature), "location": location}
        }
    
    @staticmethod
    def crop_reminder(crop_name: str, action: str, days_remaining: int) -> Dict:
        return {
            "title": f"Crop Reminder: {crop_name} 🌾",
            "body": f"Time for {action} in {days_remaining} days",
            "data": {"type": "crop_reminder", "crop_name": crop_name, "action": action, "days": str(days_remaining)}
        }
    
    @staticmethod
    def harvest_ready(crop_name: str, field_name: str) -> Dict:
        return {
            "title": "Harvest Ready! 🎉",
            "body": f"Your {crop_name} in {field_name} is ready for harvest",
            "data": {"type": "harvest", "crop_name": crop_name, "field_name": field_name}
        }
    
    @staticmethod
    def disease_alert(crop_name: str, disease_name: str, severity: str) -> Dict:
        return {
            "title": f"Disease Alert: {disease_name} ⚠️",
            "body": f"{severity} severity detected in {crop_name}. Take immediate action!",
            "data": {"type": "disease", "crop_name": crop_name, "disease": disease_name, "severity": severity}
        }
    
    @staticmethod
    def irrigation_reminder(field_name: str, moisture_level: float) -> Dict:
        return {
            "title": "Irrigation Needed 💧",
            "body": f"{field_name} moisture level is {moisture_level}%. Time to water!",
            "data": {"type": "irrigation", "field_name": field_name, "moisture": str(moisture_level)}
        }


def get_notification_template(template_type: str, **kwargs) -> Optional[Dict]:
    """
    Get a pre-defined notification template
    
    Args:
        template_type: Type of notification template
        **kwargs: Template-specific parameters
    
    Returns:
        Dict with notification data or None if template not found
    """
    templates = {
        "welcome": NotificationTemplates.welcome_notification,
        "weather": NotificationTemplates.weather_alert,
        "crop_reminder": NotificationTemplates.crop_reminder,
        "harvest": NotificationTemplates.harvest_ready,
        "disease": NotificationTemplates.disease_alert,
        "irrigation": NotificationTemplates.irrigation_reminder,
    }
    
    if template_type not in templates:
        logger.error(f"Unknown notification template: {template_type}")
        return None
    
    try:
        return templates[template_type](**kwargs)
    except TypeError as e:
        logger.error(f"Invalid parameters for template {template_type}: {e}")
        return None


# Convenience function for backward compatibility
def send_push_notification(fcm_token: str, title: str, body: str, data: Optional[Dict] = None) -> bool:
    """
    Simplified function to send a push notification (backward compatibility)
    
    Args:
        fcm_token: FCM token
        title: Notification title
        body: Notification body
        data: Optional data payload
    
    Returns:
        bool: True if successful
    """
    success, _ = send_notification(fcm_token, title, body, data)
    return success


# Initialize Firebase Admin SDK when module is imported (non-blocking)
if __name__ != "__main__":
    try:
        initialize_firebase_admin()
    except Exception as e:
        logger.warning(f"Firebase initialization on import failed (will retry on first use): {e}")
def send_data_message(
    fcm_token: str,
    data: Dict,
    priority: str = "high",
    timeout: int = 30
) -> Tuple[bool, Dict]:
    """
    Send a data-only message (no notification, app handles it)
    
    Args:
        fcm_token: The FCM token of the target device
        data: Custom data payload
        priority: Message priority ('high' or 'normal')
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success: bool, response: Dict)
    """
    
    if not validate_fcm_config():
        return False, {"error": "FCM not properly configured"}
    
    if not fcm_token or not fcm_token.strip():
        logger.error("Empty FCM token provided")
        return False, {"error": "Invalid FCM token"}
    
    if not data:
        logger.error("Data payload is required for data messages")
        return False, {"error": "Data payload is required"}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={FIREBASE_SERVER_KEY}'
    }
    
    payload = {
        'to': fcm_token.strip(),
        'data': {k: str(v) for k, v in data.items()},
        'priority': priority,
        'content_available': True
    }
    
    try:
        logger.info(f"Sending data message to token: {fcm_token[:10]}...")
        
        response = requests.post(
            FCM_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout
        )
        
        response_data = response.json()
        
        if response.status_code == 200:
            if response_data.get('success', 0) > 0:
                logger.info("Data message sent successfully")
                return True, response_data
            else:
                error_msg = "FCM data message failed"
                logger.error(error_msg)
                return False, {"error": error_msg, "fcm_response": response_data}
        else:
            error_msg = f"HTTP {response.status_code}: {response_data.get('error', 'Unknown error')}"
            logger.error(f"Data message request failed: {error_msg}")
            return False, {"error": error_msg, "status_code": response.status_code}
            
    except Exception as e:
        error_msg = f"Data message error: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg}


# Enhanced notification templates with proper error handling
class NotificationTemplates:
    """Enhanced notification templates for Smart Farmer with validation"""
    
    @staticmethod
    def _validate_template_params(**kwargs) -> bool:
        """Validate template parameters"""
        for key, value in kwargs.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                logger.error(f"Invalid template parameter: {key} = {value}")
                return False
        return True
    
    @staticmethod
    def weather_alert(severity: str, message: str, location: str = None) -> Dict:
        """Weather alert notification with validation"""
        if not NotificationTemplates._validate_template_params(severity=severity, message=message):
            raise ValueError("Invalid parameters for weather alert template")
        
        severity_upper = severity.upper()
        icon = "⚠️" if severity_upper in ["HIGH", "CRITICAL"] else "🌤️"
        location_text = f" in {location}" if location else ""
        
        return {
            'title': f'{icon} Weather Alert - {severity_upper}',
            'body': f'{message}{location_text}',
            'data': {
                'type': 'weather',
                'severity': severity.lower(),
                'location': location or '',
                'action': 'open_weather',
                'timestamp': str(int(time.time()))
            },
            'priority': 'high' if severity_upper in ["HIGH", "CRITICAL"] else 'normal'
        }
    
    @staticmethod
    def irrigation_reminder(moisture_level: str, field_name: str = None) -> Dict:
        """Irrigation reminder notification with validation"""
        if not NotificationTemplates._validate_template_params(moisture_level=moisture_level):
            raise ValueError("Invalid parameters for irrigation reminder template")
        
        field_text = f" for {field_name}" if field_name else ""
        
        return {
            'title': '💧 Irrigation Needed',
            'body': f'Soil moisture is at {moisture_level}{field_text}. Time to water your crops.',
            'data': {
                'type': 'irrigation',
                'moisture_level': moisture_level,
                'field_name': field_name or '',
                'action': 'open_irrigation',
                'timestamp': str(int(time.time()))
            },
            'priority': 'high'
        }
    
    @staticmethod
    def crop_health_alert(field_name: str, issue: str, severity: str = "medium") -> Dict:
        """Crop health alert notification with validation"""
        if not NotificationTemplates._validate_template_params(field_name=field_name, issue=issue):
            raise ValueError("Invalid parameters for crop health alert template")
        
        icon = "🚨" if severity == "critical" else "🌱"
        urgency_text = "Check immediately!" if severity == "critical" else "Please investigate."
        
        return {
            'title': f'{icon} Crop Health Alert',
            'body': f'{issue} detected in {field_name}. {urgency_text}',
            'data': {
                'type': 'health',
                'field': field_name,
                'issue': issue,
                'severity': severity,
                'action': 'open_field_details',
                'timestamp': str(int(time.time()))
            },
            'priority': 'high' if severity == "critical" else 'normal'
        }
    
    @staticmethod
    def market_price_update(crop: str, change: str, current_price: str = None) -> Dict:
        """Market price update notification with validation"""
        if not NotificationTemplates._validate_template_params(crop=crop, change=change):
            raise ValueError("Invalid parameters for market price update template")
        
        price_text = f" Current price: {current_price}" if current_price else ""
        icon = "📈" if "increase" in change.lower() or "up" in change.lower() else "📉"
        
        return {
            'title': f'{icon} Market Price Update',
            'body': f'{crop} prices {change}.{price_text} Check current rates.',
            'data': {
                'type': 'market',
                'crop': crop,
                'change': change,
                'current_price': current_price or '',
                'action': 'open_market',
                'timestamp': str(int(time.time()))
            },
            'priority': 'normal'
        }
    
    @staticmethod
    def harvest_reminder(crop: str, days_left: int, field_name: str = None) -> Dict:
        """Harvest reminder notification with validation"""
        if not NotificationTemplates._validate_template_params(crop=crop, days_left=days_left):
            raise ValueError("Invalid parameters for harvest reminder template")
        
        if not isinstance(days_left, int) or days_left < 0:
            raise ValueError("days_left must be a non-negative integer")
        
        field_text = f" in {field_name}" if field_name else ""
        urgency = "🔥" if days_left <= 2 else "🌾"
        
        if days_left == 0:
            body_text = f'{crop}{field_text} is ready for harvest today!'
        elif days_left == 1:
            body_text = f'{crop}{field_text} will be ready for harvest tomorrow.'
        else:
            body_text = f'{crop}{field_text} will be ready for harvest in {days_left} days.'
        
        return {
            'title': f'{urgency} Harvest Reminder',
            'body': body_text,
            'data': {
                'type': 'harvest',
                'crop': crop,
                'days_left': str(days_left),
                'field_name': field_name or '',
                'action': 'open_harvest_schedule',
                'timestamp': str(int(time.time()))
            },
            'priority': 'high' if days_left <= 2 else 'normal'
        }
    
    @staticmethod
    def general_message(title: str, message: str, action: str = "open_home") -> Dict:
        """General notification template with validation"""
        if not NotificationTemplates._validate_template_params(title=title, message=message):
            raise ValueError("Invalid parameters for general message template")
        
        return {
            'title': title,
            'body': message,
            'data': {
                'type': 'general',
                'action': action,
                'timestamp': str(int(time.time()))
            },
            'priority': 'normal'
        }
    
    @staticmethod
    def system_maintenance(start_time: str, duration: str = None) -> Dict:
        """System maintenance notification"""
        if not NotificationTemplates._validate_template_params(start_time=start_time):
            raise ValueError("Invalid parameters for maintenance notification")
        
        duration_text = f" for {duration}" if duration else ""
        
        return {
            'title': '🔧 Scheduled Maintenance',
            'body': f'System maintenance scheduled at {start_time}{duration_text}. Some features may be unavailable.',
            'data': {
                'type': 'maintenance',
                'start_time': start_time,
                'duration': duration or '',
                'action': 'open_home',
                'timestamp': str(int(time.time()))
            },
            'priority': 'normal'
        }


# Enhanced convenience functions with better error handling
def notify_weather_alert(fcm_token: str, severity: str, message: str, location: str = None) -> Tuple[bool, Dict]:
    """Send weather alert to user with enhanced error handling"""
    try:
        template = NotificationTemplates.weather_alert(severity, message, location)
        return send_notification(
            fcm_token=fcm_token,
            title=template['title'],
            body=template['body'],
            data=template['data'],
            priority=template['priority']
        )
    except Exception as e:
        logger.error(f"Failed to send weather alert: {str(e)}")
        return False, {"error": str(e)}


def notify_irrigation_needed(fcm_token: str, moisture_level: str, field_name: str = None) -> Tuple[bool, Dict]:
    """Send irrigation reminder to user with enhanced error handling"""
    try:
        template = NotificationTemplates.irrigation_reminder(moisture_level, field_name)
        return send_notification(
            fcm_token=fcm_token,
            title=template['title'],
            body=template['body'],
            data=template['data'],
            priority=template['priority']
        )
    except Exception as e:
        logger.error(f"Failed to send irrigation reminder: {str(e)}")
        return False, {"error": str(e)}


def notify_crop_health_issue(fcm_token: str, field_name: str, issue: str, severity: str = "medium") -> Tuple[bool, Dict]:
    """Send crop health alert to user with enhanced error handling"""
    try:
        template = NotificationTemplates.crop_health_alert(field_name, issue, severity)
        return send_notification(
            fcm_token=fcm_token,
            title=template['title'],
            body=template['body'],
            data=template['data'],
            priority=template['priority']
        )
    except Exception as e:
        logger.error(f"Failed to send crop health alert: {str(e)}")
        return False, {"error": str(e)}


def notify_market_update(fcm_token: str, crop: str, change: str, current_price: str = None) -> Tuple[bool, Dict]:
    """Send market price update to user with enhanced error handling"""
    try:
        template = NotificationTemplates.market_price_update(crop, change, current_price)
        return send_notification(
            fcm_token=fcm_token,
            title=template['title'],
            body=template['body'],
            data=template['data'],
            priority=template['priority']
        )
    except Exception as e:
        logger.error(f"Failed to send market update: {str(e)}")
        return False, {"error": str(e)}


def notify_harvest_reminder(fcm_token: str, crop: str, days_left: int, field_name: str = None) -> Tuple[bool, Dict]:
    """Send harvest reminder to user with enhanced error handling"""
    try:
        template = NotificationTemplates.harvest_reminder(crop, days_left, field_name)
        return send_notification(
            fcm_token=fcm_token,
            title=template['title'],
            body=template['body'],
            data=template['data'],
            priority=template['priority']
        )
    except Exception as e:
        logger.error(f"Failed to send harvest reminder: {str(e)}")
        return False, {"error": str(e)}


def broadcast_to_all_users(db_session, title: str, message: str, user_type: str = "all") -> Tuple[bool, Dict]:
    """
    Send notification to users with comprehensive error handling and detailed reporting
    
    Args:
        db_session: SQLAlchemy database session
        title: Notification title
        message: Notification message
        user_type: Type of users to notify ('all', 'app_user', 'seller')
    
    Returns:
        Tuple of (success: bool, response: Dict)
    """
    try:
        from main import AppUser, Seller  # Import your models
        
        fcm_tokens = []
        user_count = 0
        
        if user_type in ["all", "app_user"]:
            # Get app users with FCM tokens
            app_users = db_session.query(AppUser).filter(
                AppUser.is_deleted == False,
                AppUser.is_banned == False,
                AppUser.fcm_token.isnot(None),
                AppUser.fcm_token != ''
            ).all()
            
            fcm_tokens.extend([user.fcm_token for user in app_users])
            user_count += len(app_users)
            logger.info(f"Found {len(app_users)} app users with FCM tokens")
        
        if user_type in ["all", "seller"]:
            # Get sellers with FCM tokens
            sellers = db_session.query(Seller).filter(
                Seller.is_active == True,
                Seller.fcm_token.isnot(None),
                Seller.fcm_token != ''
            ).all()
            
            fcm_tokens.extend([seller.fcm_token for seller in sellers])
            user_count += len(sellers)
            logger.info(f"Found {len(sellers)} sellers with FCM tokens")
        
        if not fcm_tokens:
            logger.warning("No users found with valid FCM tokens")
            return False, {
                "error": "No users found with valid FCM tokens",
                "total_users": user_count,
                "tokens_found": 0
            }
        
        # Send multicast notification
        success, result = send_multicast_notification(
            fcm_tokens=fcm_tokens,
            title=title,
            body=message,
            data={'type': 'broadcast', 'user_type': user_type}
        )
        
        response = {
            "total_users": user_count,
            "tokens_sent": len(fcm_tokens),
            "broadcast_success": success,
            **result
        }
        
        logger.info(f"Broadcast completed: {response}")
        return success, response
        
    except Exception as e:
        error_msg = f"Failed to broadcast notification: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg}


# Add missing import
import time
