"""
Firebase Cloud Messaging (FCM) Utility
Send push notifications to mobile app users
"""

import requests
import json
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

# Get Firebase Server Key from environment
FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY", "")
FCM_URL = "https://fcm.googleapis.com/fcm/send"


def send_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = "high"
) -> Dict:
    """
    Send a push notification to a single device
    
    Args:
        fcm_token: The FCM token of the target device
        title: Notification title
        body: Notification body/message
        data: Optional custom data payload
        priority: Notification priority ('high' or 'normal')
    
    Returns:
        Response from FCM server
    """
    
    if not FIREBASE_SERVER_KEY:
        return {"error": "Firebase Server Key not configured"}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={FIREBASE_SERVER_KEY}'
    }
    
    payload = {
        'to': fcm_token,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default',
            'badge': '1',
            'click_action': 'FLUTTER_NOTIFICATION_CLICK'
        },
        'priority': priority,
        'content_available': True
    }
    
    if data:
        payload['data'] = data
    
    try:
        response = requests.post(
            FCM_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def send_multicast_notification(
    fcm_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = "high"
) -> Dict:
    """
    Send a push notification to multiple devices
    
    Args:
        fcm_tokens: List of FCM tokens
        title: Notification title
        body: Notification body/message
        data: Optional custom data payload
        priority: Notification priority ('high' or 'normal')
    
    Returns:
        Response from FCM server
    """
    
    if not FIREBASE_SERVER_KEY:
        return {"error": "Firebase Server Key not configured"}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={FIREBASE_SERVER_KEY}'
    }
    
    payload = {
        'registration_ids': fcm_tokens,
        'notification': {
            'title': title,
            'body': body,
            'sound': 'default',
            'badge': '1',
            'click_action': 'FLUTTER_NOTIFICATION_CLICK'
        },
        'priority': priority,
        'content_available': True
    }
    
    if data:
        payload['data'] = data
    
    try:
        response = requests.post(
            FCM_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def send_data_message(
    fcm_token: str,
    data: Dict,
    priority: str = "high"
) -> Dict:
    """
    Send a data-only message (no notification, app handles it)
    
    Args:
        fcm_token: The FCM token of the target device
        data: Custom data payload
        priority: Message priority ('high' or 'normal')
    
    Returns:
        Response from FCM server
    """
    
    if not FIREBASE_SERVER_KEY:
        return {"error": "Firebase Server Key not configured"}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={FIREBASE_SERVER_KEY}'
    }
    
    payload = {
        'to': fcm_token,
        'data': data,
        'priority': priority,
        'content_available': True
    }
    
    try:
        response = requests.post(
            FCM_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Predefined notification templates
class NotificationTemplates:
    """Common notification templates for Smart Farmer"""
    
    @staticmethod
    def weather_alert(severity: str, message: str) -> Dict:
        """Weather alert notification"""
        return {
            'title': f'⚠️ Weather Alert - {severity.upper()}',
            'body': message,
            'data': {
                'type': 'weather',
                'severity': severity,
                'action': 'open_weather'
            }
        }
    
    @staticmethod
    def irrigation_reminder(moisture_level: str) -> Dict:
        """Irrigation reminder notification"""
        return {
            'title': '💧 Irrigation Needed',
            'body': f'Soil moisture is at {moisture_level}. Time to water your crops.',
            'data': {
                'type': 'irrigation',
                'moisture_level': moisture_level,
                'action': 'open_irrigation'
            }
        }
    
    @staticmethod
    def crop_health_alert(field_name: str, issue: str) -> Dict:
        """Crop health alert notification"""
        return {
            'title': '🌱 Crop Health Alert',
            'body': f'{issue} detected in {field_name}. Check immediately.',
            'data': {
                'type': 'health',
                'field': field_name,
                'issue': issue,
                'action': 'open_field_details'
            }
        }
    
    @staticmethod
    def market_price_update(crop: str, change: str) -> Dict:
        """Market price update notification"""
        return {
            'title': '📈 Market Price Update',
            'body': f'{crop} prices {change}. Check current rates.',
            'data': {
                'type': 'market',
                'crop': crop,
                'change': change,
                'action': 'open_market'
            }
        }
    
    @staticmethod
    def harvest_reminder(crop: str, days_left: int) -> Dict:
        """Harvest reminder notification"""
        return {
            'title': '🌾 Harvest Reminder',
            'body': f'{crop} will be ready for harvest in {days_left} days.',
            'data': {
                'type': 'harvest',
                'crop': crop,
                'days_left': str(days_left),
                'action': 'open_harvest_schedule'
            }
        }
    
    @staticmethod
    def general_message(title: str, message: str) -> Dict:
        """General notification"""
        return {
            'title': title,
            'body': message,
            'data': {
                'type': 'general',
                'action': 'open_home'
            }
        }


# Example usage functions
def notify_weather_alert(fcm_token: str, severity: str, message: str):
    """Send weather alert to user"""
    template = NotificationTemplates.weather_alert(severity, message)
    return send_notification(
        fcm_token=fcm_token,
        title=template['title'],
        body=template['body'],
        data=template['data']
    )


def notify_irrigation_needed(fcm_token: str, moisture_level: str):
    """Send irrigation reminder to user"""
    template = NotificationTemplates.irrigation_reminder(moisture_level)
    return send_notification(
        fcm_token=fcm_token,
        title=template['title'],
        body=template['body'],
        data=template['data']
    )


def notify_crop_health_issue(fcm_token: str, field_name: str, issue: str):
    """Send crop health alert to user"""
    template = NotificationTemplates.crop_health_alert(field_name, issue)
    return send_notification(
        fcm_token=fcm_token,
        title=template['title'],
        body=template['body'],
        data=template['data']
    )


def notify_market_update(fcm_token: str, crop: str, change: str):
    """Send market price update to user"""
    template = NotificationTemplates.market_price_update(crop, change)
    return send_notification(
        fcm_token=fcm_token,
        title=template['title'],
        body=template['body'],
        data=template['data']
    )


def notify_harvest_reminder(fcm_token: str, crop: str, days_left: int):
    """Send harvest reminder to user"""
    template = NotificationTemplates.harvest_reminder(crop, days_left)
    return send_notification(
        fcm_token=fcm_token,
        title=template['title'],
        body=template['body'],
        data=template['data']
    )


def broadcast_to_all_users(db_session, title: str, message: str):
    """
    Send notification to all active users
    
    Args:
        db_session: SQLAlchemy database session
        title: Notification title
        message: Notification message
    """
    from main import AppUser  # Import your AppUser model
    
    # Get all active users with FCM tokens
    users = db_session.query(AppUser).filter(
        AppUser.is_deleted == False,
        AppUser.is_banned == False,
        AppUser.fcm_token.isnot(None)
    ).all()
    
    fcm_tokens = [user.fcm_token for user in users if user.fcm_token]
    
    if fcm_tokens:
        # Send in batches of 1000 (FCM limit)
        batch_size = 1000
        for i in range(0, len(fcm_tokens), batch_size):
            batch = fcm_tokens[i:i + batch_size]
            send_multicast_notification(
                fcm_tokens=batch,
                title=title,
                body=message,
                data={'type': 'broadcast'}
            )
    
    return {"sent_to": len(fcm_tokens), "users": len(users)}
