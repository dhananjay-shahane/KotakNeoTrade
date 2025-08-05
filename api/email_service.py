"""
Comprehensive Email Service for Kotak Neo Trading Platform
Handles all 4 notification cases with Gmail SMTP integration
"""
import os
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
                
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
                
            if not text_content and not html_content:
                logger.error("❌ No email content provided")
                return False
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.admin_email and self.admin_password:
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
            from config.database_config import get_db_dict_connection
            
            # Get user's email preferences from external_users and user_email_settings
            conn = get_db_dict_connection()
            if not conn:
                return None
            
            try:
                with conn.cursor() as cursor:
                    # First try to get alternative email from user_email_settings
                    cursor.execute("""
                        SELECT alternative_email FROM user_email_settings 
                        WHERE username = %s AND alternative_email IS NOT NULL AND alternative_email != ''
                    """, (user_id,))
                    
                    alt_email_result = cursor.fetchone()
                    if alt_email_result and alt_email_result[0]:
                        return alt_email_result[0]
                    
                    # If no alternative email, get regular email from external_users
                    cursor.execute("""
                        SELECT email FROM external_users 
                        WHERE username = %s AND email IS NOT NULL AND email != ''
                    """, (user_id,))
                    
                    email_result = cursor.fetchone()
                    if email_result and email_result[0]:
                        return email_result[0]
                    
                    return None
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting user email preference: {e}")
            
        return None
    
    # Case 1: Trade Signal Notification to External Users
    def send_trade_signal_notification(self, signal_data: Dict[str, Any]) -> bool:
        """Send new trade signal notifications to all external users"""
        try:
            from config.database_config import execute_db_query
            
            # Get all external users
            query = "SELECT email FROM external_users WHERE email IS NOT NULL"
            external_users = execute_db_query(query)
            
            if not external_users:
                logger.info("No external users found for trade signal notification")
                return True
                
            subject = f"🚨 New Trading Signal: {signal_data.get('symbol', 'N/A')}"
            
            # Create email content
            html_content = self._create_trade_signal_html_template(signal_data)
            text_content = self._create_trade_signal_text_template(signal_data)
            
            success_count = 0
            for user in external_users:
                email = user.get('email')
                if email and self.send_email(email, subject, text_content, html_content):
                    success_count += 1
                    
            logger.info(f"✅ Trade signal notification sent to {success_count}/{len(external_users)} external users")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to send trade signal notifications: {e}")
            return False
    
    # Case 2: Deal Creation Notification to Logged-in User
    def send_deal_creation_notification(self, user_id: str, deal_data: Dict[str, Any]) -> bool:
        """Send deal creation notification to logged-in user"""
        try:
            user_email = self.get_user_email_preference(user_id)
            if not user_email:
                logger.error(f"No email found for user: {user_id}")
                return False
                
            subject = f"✅ Deal Created: {deal_data.get('symbol', 'N/A')}"
            
            # Create email content
            html_content = self._create_deal_html_template(deal_data, 'created')
            text_content = self._create_deal_text_template(deal_data, 'created')
            
            success = self.send_email(user_email, subject, text_content, html_content)
            if success:
                logger.info(f"✅ Deal creation notification sent to {user_email}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to send deal creation notification: {e}")
            return False
    
    # Case 3: Daily Trading Signal Change Email (Subscription-Based)
    def setup_daily_trading_updates(self, user_id: str, send_time: str = "09:00"):
        """Setup daily trading update emails for subscribed users"""
        try:
            # Schedule daily email at specified time
            schedule.every().day.at(send_time).do(
                self._send_daily_trading_update, user_id
            )
            logger.info(f"✅ Daily trading updates scheduled for {user_id} at {send_time}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup daily trading updates: {e}")
    
    def _send_daily_trading_update(self, user_id: str) -> bool:
        """Send daily trading signal changes to subscribed users"""
        try:
            from config.database_config import execute_db_query
            
            # Check if user has subscription enabled
            user_query = """
            SELECT email, alternative_email, subscription 
            FROM users WHERE username = %s AND subscription = true
            """
            user_result = execute_db_query(user_query, (user_id,))
            
            if not user_result:
                return False
                
            user_data = user_result[0]
            user_email = user_data.get('alternative_email') or user_data.get('email')
            
            if not user_email:
                return False
                
            # Check if daily email already sent
            if not self._can_send_daily_email(user_email):
                logger.info(f"Daily email already sent to {user_email} today")
                return True
                
            # Get today's signal changes
            today = datetime.now().date()
            signal_query = """
            SELECT symbol, action, entry_price, target_price, created_at
            FROM admin_trade_signals 
            WHERE DATE(created_at) = %s
            ORDER BY created_at DESC
            """
            signal_changes = execute_db_query(signal_query, (today,))
            
            if not signal_changes:
                logger.info(f"No signal changes today for {user_email}")
                return True
                
            subject = f"📈 Daily Trading Update - {today.strftime('%Y-%m-%d')}"
            
            # Create email content
            html_content = self._create_daily_update_html_template(signal_changes)
            text_content = self._create_daily_update_text_template(signal_changes)
            
            success = self.send_email(user_email, subject, text_content, html_content)
            if success:
                logger.info(f"✅ Daily trading update sent to {user_email}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to send daily trading update: {e}")
            return False
    
    # Case 4: Deal Status Email Notification (Opt-in)
    def send_deal_status_notification(self, user_id: str, deal_data: Dict[str, Any], action: str) -> bool:
        """Send deal status notification (close/delete) if user has opted in"""
        try:
            from config.database_config import execute_db_query
            
            # Check if user has email notifications enabled
            query = """
            SELECT email, alternative_email, email_notification 
            FROM external_users 
            WHERE username = %s AND email_notification = true
            """
            result = execute_db_query(query, (user_id,))
            
            if not result:
                logger.info(f"User {user_id} has not opted in for email notifications")
                return True
                
            user_data = result[0]
            user_email = user_data.get('alternative_email') or user_data.get('email')
            
            if not user_email:
                logger.error(f"No email found for user: {user_id}")
                return False
                
            action_text = "Closed" if action == 'closed' else "Deleted"
            subject = f"📊 Deal {action_text}: {deal_data.get('symbol', 'N/A')}"
            
            # Create email content
            html_content = self._create_deal_html_template(deal_data, action)
            text_content = self._create_deal_text_template(deal_data, action)
            
            success = self.send_email(user_email, subject, text_content, html_content)
            if success:
                logger.info(f"✅ Deal {action} notification sent to {user_email}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to send deal status notification: {e}")
            return False
    
    # Email Template Methods
    def _create_trade_signal_html_template(self, signal_data: Dict[str, Any]) -> str:
        """Create HTML template for trade signal notifications"""
        template_str = """
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">🚨 New Trading Signal</h2>
                
                <div style="background-color: #3498db; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin: 0; font-size: 28px;">{{ symbol }}</h3>
                    <p style="margin: 5px 0 0 0; font-size: 18px;">{{ action|upper }}</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="color: #495057; margin-top: 0;">Signal Details</h3>
                    <p><strong>Entry Price:</strong> ₹{{ entry_price }}</p>
                    {% if target_price %}<p><strong>Target Price:</strong> ₹{{ target_price }}</p>{% endif %}
                    {% if stop_loss %}<p><strong>Stop Loss:</strong> ₹{{ stop_loss }}</p>{% endif %}
                    <p><strong>Signal Time:</strong> {{ created_at }}</p>
                </div>
                
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 20px;">
                    This is an automated notification from Kotak Neo Trading Platform.<br>
                    You are receiving this because you are subscribed to trading signal alerts.
                </p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(**signal_data)
    
    def _create_trade_signal_text_template(self, signal_data: Dict[str, Any]) -> str:
        """Create text template for trade signal notifications"""
        text = f"""
🚨 NEW TRADING SIGNAL

Symbol: {signal_data.get('symbol', 'N/A')}
Action: {signal_data.get('action', 'N/A').upper()}
Entry Price: ₹{signal_data.get('entry_price', 'N/A')}
"""
        
        if signal_data.get('target_price'):
            text += f"Target Price: ₹{signal_data.get('target_price')}\n"
            
        if signal_data.get('stop_loss'):
            text += f"Stop Loss: ₹{signal_data.get('stop_loss')}\n"
            
        text += f"Signal Time: {signal_data.get('created_at', 'N/A')}\n"
        text += """
---
Kotak Neo Trading Platform
This is an automated trading signal notification.
        """.strip()
        
        return text
    
    def _create_deal_html_template(self, deal_data: Dict[str, Any], action: str) -> str:
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
                <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 Deal {{{{ action.title() }}}}</h2>
                
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
                    {{% if target_price %}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Target Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{{{ target_price }}}}</td>
                    </tr>
                    {{% endif %}}
                    {{% if exit_price %}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Exit Price:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{{{{ exit_price }}}}</td>
                    </tr>
                    {{% endif %}}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold;">Date:</td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{{{{ date }}}}</td>
                    </tr>
                </table>
                
                {{% if profit_loss is not none %}}
                <div style="background-color: {{{{ '#d5edda' if profit_loss >= 0 else '#f8d7da' }}}}; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: {{{{ '#155724' if profit_loss >= 0 else '#721c24' }}}};">
                        {{{{ 'Profit' if profit_loss >= 0 else 'Loss' }}}}:
                    </h4>
                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: {{{{ '#155724' if profit_loss >= 0 else '#721c24' }}}};">
                        ₹{{{{ profit_loss }}}}
                    </p>
                </div>
                {{% endif %}}
                
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px; border-top: 1px solid #dee2e6; padding-top: 20px;">
                    This is an automated notification from your trading platform.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(action=action, **deal_data)
    
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
        
        profit_loss = deal_data.get('profit_loss')
        if profit_loss is not None:
            text += f"\n{'Profit' if profit_loss >= 0 else 'Loss'}: ₹{profit_loss}\n"
            
        text += """
---
Kotak Neo Trading Platform
This is an automated notification. Please do not reply.
        """.strip()
        
        return text
    
    def _create_daily_update_html_template(self, signal_changes: List[Dict[str, Any]]) -> str:
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