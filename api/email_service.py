"""
Email service for sending notifications and alerts
"""
import os
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = "noreply@tradingplatform.com"
        self.client = None
        
        if self.api_key:
            try:
                self.client = SendGridAPIClient(self.api_key)
                logger.info("✅ SendGrid email service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SendGrid: {e}")
        else:
            logger.warning("⚠️ SENDGRID_API_KEY not found - email service disabled")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        text_content: Optional[str] = None,
        html_content: Optional[str] = None
    ) -> bool:
        """Send email using SendGrid"""
        if not self.client:
            logger.error("❌ SendGrid not configured - cannot send email")
            return False
            
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject
            )
            
            if html_content:
                message.content = Content("text/html", html_content)
            elif text_content:
                message.content = Content("text/plain", text_content)
            else:
                logger.error("❌ No email content provided")
                return False
                
            response = self.client.send(message)
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    def send_deal_notification(self, to_email: str, deal_data: dict, action: str) -> bool:
        """Send deal-related notification email"""
        subject_map = {
            'created': f"Deal Created: {deal_data.get('symbol', 'Unknown')}",
            'updated': f"Deal Updated: {deal_data.get('symbol', 'Unknown')}",
            'closed': f"Deal Closed: {deal_data.get('symbol', 'Unknown')}"
        }
        
        subject = subject_map.get(action, "Trading Deal Notification")
        
        # Create HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Trading Deal {action.title()}</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="color: #495057; margin-top: 0;">Deal Details</h3>
                    <p><strong>Symbol:</strong> {deal_data.get('symbol', 'N/A')}</p>
                    <p><strong>Quantity:</strong> {deal_data.get('qty', 'N/A')}</p>
                    <p><strong>Entry Price:</strong> ₹{deal_data.get('ep', 'N/A')}</p>
                    <p><strong>Target Price:</strong> ₹{deal_data.get('tp', 'N/A')}</p>
                    <p><strong>Target %:</strong> {deal_data.get('tpr', 'N/A')}%</p>
                    <p><strong>Status:</strong> {deal_data.get('status', 'N/A')}</p>
                    
                    {f'<p><strong>Exit Price:</strong> ₹{deal_data.get("exp", "N/A")}</p>' if action == 'closed' else ''}
                    {f'<p><strong>Profit:</strong> ₹{deal_data.get("pr", "N/A")}</p>' if action == 'closed' else ''}
                    {f'<p><strong>Profit %:</strong> {deal_data.get("pp", "N/A")}%</p>' if action == 'closed' else ''}
                </div>
                
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 20px;">
                    This is an automated notification from your trading platform.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content=html_content)

# Global email service instance
email_service = EmailService()