import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)

def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """
    Send an email using SMTP
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("SMTP credentials not configured. Email not sent.")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_password_reset_email(to_email: str, token: str):
    """
    Send password reset email with token
    """
    # In a real app, this would be a link to your frontend
    reset_link = f"https://smart-farmer-app.com/reset-password?token={token}"
    
    subject = "Smart Farmer - Password Reset"
    body = f"""
    <h2>Password Reset Request</h2>
    <p>You requested a password reset for your Smart Farmer account.</p>
    <p>Please use the following token to reset your password:</p>
    <h3 style="background-color: #f0f0f0; padding: 10px; display: inline-block;">{token}</h3>
    <p>Or click the link below:</p>
    <a href="{reset_link}">{reset_link}</a>
    <p>If you didn't request this, please ignore this email.</p>
    <p>This token will expire in 1 hour.</p>
    """
    
    return send_email(to_email, subject, body, is_html=True)
