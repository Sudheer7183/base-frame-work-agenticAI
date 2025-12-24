"""
Email Service - ULTRA-SIMPLE VERSION THAT WORKS

File: backend/app/services/email_service.py
This version is tested and guaranteed to work with Gmail
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import Optional
from datetime import datetime

from app.core.config import settings
import os
logger = logging.getLogger(__name__)

FRONTEND_URL="http://localhost:3000"
SMTP_FROM_NAME="Agentic AI Platform"
SMTP_FROM_EMAIL="psudheer854@gmail.com"
SMTP_PASSWORD="wwbrpqmdrqytcczo"
SMTP_USER="psudheer854@gmail.com"
SMTP_PORT=587
SMTP_HOST="smtp.gmail.com"

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
        self.frontend_url = FRONTEND_URL
        
        # Log configuration (without password)
        logger.info(f"Email Service initialized:")
        logger.info(f"  SMTP Host: {self.smtp_host}")
        logger.info(f"  SMTP Port: {self.smtp_port}")
        logger.info(f"  SMTP User: {self.smtp_user}")
        logger.info(f"  From Email: {self.from_email}")
        logger.info(f"  Password length: {len(self.smtp_password)} chars")
    
    async def send_invitation_email(
        self,
        recipient_email: str,
        invitation_token: str,
        tenant_name: str,
        invited_by_name: str,
        invited_by_email: str,
        recipient_name: Optional[str] = None,
        roles: Optional[list] = None,
        custom_message: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Send user invitation email"""
        try:
            logger.info(f"Preparing invitation email for {recipient_email}")
            
            # Build invitation URL
            invitation_url = f"{self.frontend_url}/accept-invitation?token={invitation_token}"
            
            # Create simple email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"You've been invited to {tenant_name}"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient_email
            
            # Simple plain text body
            text_body = f"""
Hi {recipient_name or 'there'},

{invited_by_name} has invited you to join {tenant_name}.

Click here to accept: {invitation_url}

Roles: {', '.join(roles or ['USER'])}
Expires: {expires_at.strftime('%B %d, %Y') if expires_at else '7 days'}

Best regards,
{tenant_name} Team
"""
            
            # Simple HTML body
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>You've been invited to {tenant_name}!</h2>
    <p>Hi {recipient_name or 'there'},</p>
    <p>{invited_by_name} has invited you to join {tenant_name}.</p>
    <p style="margin: 30px 0;">
        <a href="{invitation_url}" 
           style="background: #667eea; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            Accept Invitation
        </a>
    </p>
    <p><strong>Roles:</strong> {', '.join(roles or ['USER'])}</p>
    <p><strong>Expires:</strong> {expires_at.strftime('%B %d, %Y') if expires_at else '7 days from now'}</p>
    <hr style="margin: 30px 0;">
    <p style="color: #666; font-size: 12px;">
        If you can't click the button, copy this link:<br>
        {invitation_url}
    </p>
</body>
</html>
"""
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email using the SIMPLE method
            logger.info(f"Sending email to {recipient_email}...")
            self._send_smtp_simple(msg)
            
            logger.info(f"✅ Invitation email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send invitation email to {recipient_email}: {e}", exc_info=True)
            return False
    
    def _send_smtp_simple(self, msg: MIMEMultipart):
        """
        Send email via SMTP - ULTRA-SIMPLE VERSION
        
        This version uses a completely different approach that works reliably.
        """
        logger.info("=== Starting SMTP connection ===")
        logger.info(f"Connecting to {self.smtp_host}:{self.smtp_port}")
        
        # Remove any spaces from password (common copy-paste issue)
        password = self.smtp_password.replace(' ', '')
        
        try:
            # Method 1: Try with SSL context (most reliable for Gmail)
            logger.info("Attempting SMTP with SSL context...")
            
            context = ssl.create_default_context()
            
            # Connect without using 'with' statement
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.set_debuglevel(1)  # Enable debug output
            
            logger.info("Connected, starting TLS...")
            server.starttls(context=context)
            
            logger.info("TLS started, logging in...")
            server.login(self.smtp_user, password)
            
            logger.info("Logged in, sending message...")
            server.send_message(msg)
            
            logger.info("Message sent, closing connection...")
            server.quit()
            
            logger.info("✅ SMTP send successful!")
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("❌ SMTP Authentication Failed!")
            logger.error("This usually means:")
            logger.error("1. Wrong password (check your App Password)")
            logger.error("2. 2FA not enabled on Gmail")
            logger.error("3. App Password not generated")
            logger.error(f"Error details: {e}")
            raise Exception(f"SMTP authentication failed. Check your Gmail App Password. Error: {e}")
            
        except smtplib.SMTPConnectError as e:
            logger.error("❌ Could not connect to SMTP server")
            logger.error(f"Error: {e}")
            raise Exception(f"Could not connect to {self.smtp_host}:{self.smtp_port}")
            
        except Exception as e:
            logger.error(f"❌ SMTP send failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Try alternative method
            logger.info("Trying alternative SMTP method...")
            try:
                self._send_smtp_alternative(msg)
            except Exception as e2:
                logger.error(f"Alternative method also failed: {e2}")
                raise Exception(f"Email sending failed: {e}")
    
    def _send_smtp_alternative(self, msg: MIMEMultipart):
        """
        Alternative SMTP sending method using smtplib.SMTP_SSL
        Sometimes this works when regular SMTP doesn't
        """
        logger.info("=== Trying alternative SMTP_SSL method ===")
        
        # For Gmail, can also use port 465 with SMTP_SSL
        password = self.smtp_password.replace(' ', '')
        
        try:
            context = ssl.create_default_context()
            
            # Use SMTP_SSL on port 465 instead
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.set_debuglevel(1)
                server.login(self.smtp_user, password)
                server.send_message(msg)
                logger.info("✅ Alternative method successful!")
                
        except Exception as e:
            logger.error(f"Alternative method failed: {e}")
            raise


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service