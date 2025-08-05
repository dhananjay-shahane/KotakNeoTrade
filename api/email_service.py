"""
Comprehensive Email Service for Kotak Neo Trading Platform
Handles all notification cases with Gmail SMTP integration
"""
import os
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Optional, List, Dict, Any
from jinja2 import Template
import schedule
import time
import threading

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """Initialize comprehensive email service with Gmail SMTP"""
        # Gmail SMTP configuration from environment
        self.smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('MAIL_PORT', 587))
        self.use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        self.admin_email = os.environ.get('EMAIL_USER')
        self.admin_password = os.environ.get('EMAIL_PASSWORD')
        self.from_email = os.environ.get('MAIL_DEFAULT_SENDER', self.admin_email)
        
        # Service status
        self.is_configured = bool(self.admin_email and self.admin_password)
        
        if self.is_configured:
            logger.info(f"✅ Email service configured for: {self.admin_email}")
        else:
            logger.warning("⚠️ Email credentials not found - email service disabled")
            
        # Track daily emails to prevent spam
        self.daily_email_tracker = {}
        
        # Initialize scheduled email system
        self._setup_daily_scheduler()
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        text_content: Optional[str] = None,
        html_content: Optional[str] = None
    ) -> bool:
        """Send email using Gmail SMTP"""
        if not self.is_configured:
            logger.error("❌ Email service not configured - cannot send email")
            return False
            
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add content
            if text_content:
                text_part = MimeText(text_content, 'plain')
                msg.attach(text_part)
                
            if html_content:
                html_part = MimeText(html_content, 'html')
                msg.attach(html_part)
                
            if not text_content and not html_content:
                logger.error("❌ No email content provided")
                return False
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.admin_email, self.admin_password)
                server.send_message(msg)
                
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    def _setup_daily_scheduler(self):
        """Setup daily email scheduler for subscription-based notifications"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def _can_send_daily_email(self, email: str) -> bool:
        """Check if daily email can be sent (max one per day)"""
        today = datetime.now().date()
        last_sent = self.daily_email_tracker.get(email)
        
        if not last_sent or last_sent < today:
            self.daily_email_tracker[email] = today
            return True
        return False
    
    def get_user_email_preference(self, user_id: str) -> Optional[str]:
        """Get user's preferred email address"""
        try:
            from config.database_config import execute_db_query
            
            # Check if user has alternative email set
            query = """
            SELECT email, alternative_email FROM users WHERE username = %s
            """
            result = execute_db_query(query, (user_id,))
            
            if result:
                user_data = result[0]
                # Return alternative email if set, otherwise regular email
                return user_data.get('alternative_email') or user_data.get('email')
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user email preference: {e}")
            return None
    
    def get_subscribed_users(self) -> List[Dict[str, Any]]:
        """Get all users with email subscription enabled"""
        try:
            from config.database_config import execute_db_query
            
            query = """
            SELECT username, email, alternative_email, daily_email_time 
            FROM users 
            WHERE subscription = true
            """
            return execute_db_query(query) or []
            
        except Exception as e:
            logger.error(f"Error fetching subscribed users: {e}")
            return []
    
    def get_external_users(self) -> List[Dict[str, Any]]:
        """Get all external users for signal notifications"""
        try:
            from config.database_config import execute_db_query
            
            query = """
            SELECT email FROM external_users WHERE email_notification = true
            """
            return execute_db_query(query) or []
            
        except Exception as e:
            logger.error(f"Error fetching external users: {e}")
            return []
    
    # ========================================
    # NOTIFICATION CASE 1: Trade Signal to External Users
    # ========================================
    
    def send_trade_signal_notification(self, signal_data: Dict[str, Any]) -> bool:
        """Send new trade signal notification to all external users"""
        try:
            external_users = self.get_external_users()
            
            if not external_users:
                logger.info("No external users with email notifications enabled")
                return True
                
            subject = f"New Trading Signal: {signal_data.get('symbol', 'Unknown Symbol')}"
            
            html_content = self._create_signal_email_template(signal_data)
            text_content = self._create_signal_text_template(signal_data)
            
            success_count = 0
            for user in external_users:
                if self.send_email(user['email'], subject, text_content, html_content):
                    success_count += 1
                    
            logger.info(f"✅ Signal notification sent to {success_count}/{len(external_users)} external users")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending trade signal notifications: {e}")
            return False
    
    # ========================================
    # NOTIFICATION CASE 2: Deal Creation to Logged-in User
    # ========================================
    
    def send_deal_creation_notification(self, user_id: str, deal_data: Dict[str, Any]) -> bool:
        """Send deal creation notification to logged-in user"""
        try:
            user_email = self.get_user_email_preference(user_id)
            
            if not user_email:
                logger.warning(f"No email found for user: {user_id}")
                return False
                
            subject = f"Deal Created: {deal_data.get('symbol', 'Unknown')}"
            
            html_content = self._create_deal_email_template(deal_data, 'created')
            text_content = self._create_deal_text_template(deal_data, 'created')
            
            return self.send_email(user_email, subject, text_content, html_content)
            
        except Exception as e:
            logger.error(f"Error sending deal creation notification: {e}")
            return False
    
    # ========================================
    # NOTIFICATION CASE 3: Daily Trading Signal Changes
    # ========================================
    
    def schedule_daily_emails(self, user_time: str = "09:00"):
        """Schedule daily email for a specific time"""
        schedule.every().day.at(user_time).do(self.send_daily_signal_changes)
    
    def send_daily_signal_changes(self) -> bool:
        """Send daily trading signal changes to subscribed users"""
        try:
            subscribed_users = self.get_subscribed_users()
            
            if not subscribed_users:
                logger.info("No users subscribed to daily emails")
                return True
                
            # Get daily signal changes
            signal_changes = self._get_daily_signal_changes()
            
            if not signal_changes:
                logger.info("No signal changes for today")
                return True
                
            success_count = 0
            for user in subscribed_users:
                user_email = user.get('alternative_email') or user.get('email')
                
                if not user_email or not self._can_send_daily_email(user_email):
                    continue
                    
                subject = f"Daily Trading Updates - {datetime.now().strftime('%Y-%m-%d')}"
                
                html_content = self._create_daily_update_email_template(signal_changes)
                text_content = self._create_daily_update_text_template(signal_changes)
                
                if self.send_email(user_email, subject, text_content, html_content):
                    success_count += 1
                    
            logger.info(f"✅ Daily updates sent to {success_count}/{len(subscribed_users)} users")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending daily signal changes: {e}")
            return False
    
    # ========================================
    # NOTIFICATION CASE 4: Deal Status Changes
    # ========================================
    
    def send_deal_status_notification(self, user_id: str, deal_data: Dict[str, Any], action: str) -> bool:
        """Send deal status change notification (close/delete)"""
        try:
            # Check if user has email notifications enabled
            if not self._user_has_email_notifications(user_id):
                logger.info(f"User {user_id} has email notifications disabled")
                return True
                
            user_email = self.get_user_email_preference(user_id)
            
            if not user_email:
                logger.warning(f"No email found for user: {user_id}")
                return False
                
            subject_map = {
                'closed': f"Deal Closed: {deal_data.get('symbol', 'Unknown')}",
                'deleted': f"Deal Deleted: {deal_data.get('symbol', 'Unknown')}"
            }
            
            subject = subject_map.get(action, "Deal Status Update")
            
            html_content = self._create_deal_email_template(deal_data, action)
            text_content = self._create_deal_text_template(deal_data, action)
            
            return self.send_email(user_email, subject, text_content, html_content)
            
        except Exception as e:
            logger.error(f"Error sending deal status notification: {e}")
            return False
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _user_has_email_notifications(self, user_id: str) -> bool:
        """Check if user has email notifications enabled"""
        try:
            from config.database_config import execute_db_query
            
            query = """
            SELECT email_notification FROM external_users WHERE username = %s
            """
            result = execute_db_query(query, (user_id,))
            
            if result:
                return bool(result[0].get('email_notification', False))
            return False
            
        except Exception as e:
            logger.error(f"Error checking email notification preference: {e}")
            return False
    
    def _get_daily_signal_changes(self) -> List[Dict[str, Any]]:
        """Get daily signal changes from database"""
        try:
            from config.database_config import execute_db_query
            
            # Get signals that changed in the last 24 hours
            query = """
            SELECT symbol, action, entry_price, target_price, created_at, updated_at
            FROM admin_trade_signals
            WHERE DATE(created_at) = CURRENT_DATE 
               OR DATE(updated_at) = CURRENT_DATE
            ORDER BY created_at DESC
            """
            return execute_db_query(query) or []
            
        except Exception as e:
            logger.error(f"Error fetching daily signal changes: {e}")
            return []
    
    # ========================================
    # EMAIL TEMPLATES
    # ========================================
    
    def _create_signal_email_template(self, signal_data: Dict[str, Any]) -> str:
        """Create HTML template for trading signal notifications"""
        template_str = """
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">🚀 New Trading Signal Alert</h2>
                
                <div style="background-color: #3498db; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin: 0; font-size: 24px;">{{ symbol }}</h3>
                    <p style="margin: 5px 0 0 0;">{{ action|upper }}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Entry Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{ entry_price }}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Target Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{ target_price }}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Stop Loss:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{ stop_loss }}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Date:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{{ date }}</td>
                    </tr>
                </table>
                
                {% if notes %}
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">Notes:</h4>
                    <p style="margin: 0; color: #555;">{{ notes }}</p>
                </div>
                {% endif %}
                
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px;">
                    This is an automated notification from Kotak Neo Trading Platform. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(**signal_data)
    
    def _create_signal_text_template(self, signal_data: Dict[str, Any]) -> str:
        """Create text template for trading signal notifications"""
        return f"""
New Trading Signal Alert

Symbol: {signal_data.get('symbol', 'N/A')}
Action: {signal_data.get('action', 'N/A').upper()}
Entry Price: ₹{signal_data.get('entry_price', 'N/A')}
Target Price: ₹{signal_data.get('target_price', 'N/A')}
Stop Loss: ₹{signal_data.get('stop_loss', 'N/A')}
Date: {signal_data.get('date', 'N/A')}

{f"Notes: {signal_data.get('notes', '')}" if signal_data.get('notes') else ""}

---
Kotak Neo Trading Platform
This is an automated notification. Please do not reply.
        """.strip()
    
    def _create_deal_email_template(self, deal_data: Dict[str, Any], action: str) -> str:
        """Create HTML template for deal notifications"""
        action_colors = {
            'created': '#27ae60',
            'closed': '#e74c3c',
            'deleted': '#95a5a6'
        }
        
        color = action_colors.get(action, '#3498db')
        
        template_str = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 Deal {action.title()}</h2>
                
                <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin: 0; font-size: 24px;">{{{{ symbol }}}}</h3>
                    <p style="margin: 5px 0 0 0;">Deal ID: {{{{ deal_id }}}}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Quantity:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{{{{ quantity }}}}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Entry Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{{{ entry_price }}}}</td>
                    </tr>
                    {{{% if target_price %}}}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Target Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{{{ target_price }}}}</td>
                    </tr>
                    {{{% endif %}}}}
                    {{{% if exit_price %}}}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Exit Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{{{ exit_price }}}}</td>
                    </tr>
                    {{{% endif %}}}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Date:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{{{{ date }}}}</td>
                    </tr>
                </table>
                
                {{{% if profit_loss %}}}}
                <div style="background-color: {{{{ '#d5edda' if profit_loss >= 0 else '#f8d7da' }}}}; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: {{{{ '#155724' if profit_loss >= 0 else '#721c24' }}}};">
                        {{{{ 'Profit' if profit_loss >= 0 else 'Loss' }}}}:
                    </h4>
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: {{{{ '#155724' if profit_loss >= 0 else '#721c24' }}}};">
                        ₹{{{{ profit_loss }}}}
                    </p>
                </div>
                {{{% endif %}}}}
                
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px;">
                    This is an automated notification from Kotak Neo Trading Platform. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(**deal_data)
    
    def _create_deal_text_template(self, deal_data: Dict[str, Any], action: str) -> str:
        """Create text template for deal notifications"""
        text = f"""
Deal {action.title()} Notification

Symbol: {deal_data.get('symbol', 'N/A')}
Deal ID: {deal_data.get('deal_id', 'N/A')}
Quantity: {deal_data.get('quantity', 'N/A')}
Entry Price: ₹{deal_data.get('entry_price', 'N/A')}
"""
        
        if deal_data.get('target_price'):
            text += f"Target Price: ₹{deal_data.get('target_price')}\n"
            
        if deal_data.get('exit_price'):
            text += f"Exit Price: ₹{deal_data.get('exit_price')}\n"
            
        text += f"Date: {deal_data.get('date', 'N/A')}\n"
        
        if deal_data.get('profit_loss') is not None:
            profit_loss = deal_data.get('profit_loss')
            text += f"\n{'Profit' if profit_loss >= 0 else 'Loss'}: ₹{profit_loss}\n"
            
        text += """
---
Kotak Neo Trading Platform
This is an automated notification. Please do not reply.
        """.strip()
        
        return text
    
    def _create_daily_update_email_template(self, signal_changes: List[Dict[str, Any]]) -> str:
        """Create HTML template for daily update notifications"""
        template_str = """
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">📈 Daily Trading Update</h2>
                
                <p style="color: #555; margin-bottom: 25px;">
                    Here are today's trading signal changes and updates:
                </p>
                
                {% for signal in signals %}
                <div style="border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; overflow: hidden;">
                    <div style="background-color: #3498db; color: white; padding: 10px;">
                        <strong>{{ signal.symbol }}</strong> - {{ signal.action|upper }}
                    </div>
                    <div style="padding: 15px;">
                        <p style="margin: 0 0 5px 0;"><strong>Entry:</strong> ₹{{ signal.entry_price }}</p>
                        <p style="margin: 0 0 5px 0;"><strong>Target:</strong> ₹{{ signal.target_price }}</p>
                        <p style="margin: 0;"><strong>Time:</strong> {{ signal.created_at }}</p>
                    </div>
                </div>
                {% endfor %}
                
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px;">
                    You are receiving this email because you have subscribed to daily trading updates. 
                    You can manage your preferences in the settings page.
                </p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(signals=signal_changes)
    
    def _create_daily_update_text_template(self, signal_changes: List[Dict[str, Any]]) -> str:
        """Create text template for daily update notifications"""
        text = f"""
Daily Trading Update - {datetime.now().strftime('%Y-%m-%d')}

Today's trading signal changes:

"""
        
        for signal in signal_changes:
            text += f"""
Symbol: {signal.get('symbol', 'N/A')}
Action: {signal.get('action', 'N/A').upper()}
Entry Price: ₹{signal.get('entry_price', 'N/A')}
Target Price: ₹{signal.get('target_price', 'N/A')}
Time: {signal.get('created_at', 'N/A')}
---
"""
        
        text += """
Kotak Neo Trading Platform
You are receiving this email because you have subscribed to daily trading updates.
        """.strip()
        
        return text


# Global email service instance
email_service = EmailService()
                
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