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
        """Get user's email address from external_users table"""
        try:
            from config.database_config import execute_db_query
            
            # Get user's email from external_users table only
            query = """
                SELECT email FROM external_users 
                WHERE username = %s AND email IS NOT NULL AND email != '' AND email_notification = true
            """
            result = execute_db_query(query, (user_id,))
            
            if result and len(result) > 0:
                return result[0].get('email')
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting user email preference: {e}")
            return None
    
    # Case 1: Trade Signal Notification to External Users
    def send_trade_signal_notification(self, signal_data: Dict[str, Any]) -> bool:
        """Send new trade signal notifications to external users with email notifications enabled"""
        try:
            from config.database_config import execute_db_query
            
            # Get all external users with email notifications enabled
            query = """
                SELECT email FROM external_users 
                WHERE email IS NOT NULL AND email != '' AND email_notification = true
            """
            external_users = execute_db_query(query)
            
            if not external_users:
                logger.info("No external users with email notifications enabled found")
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
    
    # Case 2: Deal Creation Notification (Using external_users table only)
    def send_deal_creation_notification(self, user_id: str, deal_data: Dict[str, Any]) -> bool:
        """Send deal creation notification email to user if they have email notifications enabled in external_users table"""
        try:
            from config.database_config import execute_db_query
            
            # Check if user has email notifications enabled in external_users table
            query = """
                SELECT email, email_notification 
                FROM external_users 
                WHERE username = %s AND email IS NOT NULL AND email != ''
            """
            result = execute_db_query(query, (user_id,))
            
            if not result:
                logger.error(f"User not found: {user_id}")
                return False
                
            user_data = result[0]
            user_email = user_data.get('email')
            email_notifications = user_data.get('email_notification', False)
            
            if not user_email:
                logger.error(f"No email found for user: {user_id}")
                return False
                
            if not email_notifications:
                logger.info(f"User {user_id} has email notifications disabled")
                return True  # Return True as this is expected behavior
                
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
        """Send deal status notification (close/delete) if user has email notifications enabled"""
        try:
            from config.database_config import execute_db_query
            
            # Check if user has email notifications enabled in external_users table
            query = """
                SELECT email, email_notification 
                FROM external_users 
                WHERE username = %s AND email IS NOT NULL AND email != ''
            """
            result = execute_db_query(query, (user_id,))
            
            if not result:
                logger.error(f"User not found: {user_id}")
                return False
                
            user_data = result[0]
            user_email = user_data.get('email')
            email_notifications = user_data.get('email_notification', False)
            
            if not user_email:
                logger.error(f"No email found for user: {user_id}")
                return False
                
            if not email_notifications:
                logger.info(f"User {user_id} has email notifications disabled")
                return True  # Return True as this is expected behavior
                
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
        """Create professional HTML template for deal notifications"""
        action_colors = {
            'created': '#28a745',
            'closed': '#dc3545',
            'deleted': '#6c757d'
        }
        
        action_icons = {
            'created': '📊',
            'closed': '📉',
            'deleted': '🗑️'
        }
        
        color = action_colors.get(action, '#007bff')
        icon = action_icons.get(action, '📊')
        
        # Calculate additional metrics
        invested_amount = deal_data.get('invested_amount', 0)
        current_value = deal_data.get('current_value', invested_amount)
        profit_loss = deal_data.get('profit_loss')
        if profit_loss is None and deal_data.get('exit_price') and deal_data.get('entry_price') and deal_data.get('quantity'):
            profit_loss = (float(deal_data['exit_price']) - float(deal_data['entry_price'])) * int(deal_data['quantity'])
        
        template_str = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Deal {{{{ action.title() }}}} Notification</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow: hidden;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); color: white; padding: 24px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 600;">{icon} Deal {{{{ action.title() }}}}</h1>
                    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Kotak Neo Trading Platform</p>
                </div>
                
                <!-- Symbol Header -->
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 0.5px;">{{{{ symbol }}}}</h2>
                    <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.95;">Deal ID: {{{{ deal_id }}}}</p>
                </div>
                
                <!-- Deal Information Table -->
                <div style="padding: 30px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; background-color: #fff;">
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 12px 16px; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Field</td>
                            <td style="padding: 12px 16px; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Value</td>
                        </tr>
                        <tr>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">User</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">{{{{ username }}}}</td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Quantity</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">{{{{ quantity }}}} shares</td>
                        </tr>
                        <tr>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Entry Price</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">₹{{{{ "%.2f"|format(entry_price|float) }}}}</td>
                        </tr>
                        {{% if target_price %}}
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Target Price</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #28a745; font-weight: 600;">₹{{{{ "%.2f"|format(target_price|float) }}}}</td>
                        </tr>
                        {{% endif %}}
                        {{% if exit_price %}}
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Exit Price</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #dc3545; font-weight: 600;">₹{{{{ "%.2f"|format(exit_price|float) }}}}</td>
                        </tr>
                        {{% endif %}}
                        <tr>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Invested Amount</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">₹{{{{ "%.2f"|format(invested_amount|float) if invested_amount else "0.00" }}}}</td>
                        </tr>
                        {{% if current_value and current_value != invested_amount %}}
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Current Value</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">₹{{{{ "%.2f"|format(current_value|float) }}}}</td>
                        </tr>
                        {{% endif %}}
                        {{% if profit_loss is not none and action in ['closed', 'deleted'] %}}
                        <tr style="background-color: {{% if profit_loss >= 0 %}}#d4edda{{% else %}}#f8d7da{{% endif %}};">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 600; color: #212529;">P&L</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 700; color: {{% if profit_loss >= 0 %}}#28a745{{% else %}}#dc3545{{% endif %}};">
                                {{% if profit_loss >= 0 %}}+{{% endif %}}₹{{{{ "%.2f"|format(profit_loss|float) }}}} ({{% if profit_loss >= 0 %}}Profit{{% else %}}Loss{{% endif %}})
                            </td>
                        </tr>
                        {{% endif %}}
                        <tr style="background-color: #f8f9fa;">
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; font-weight: 500; color: #212529;">Date</td>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #e9ecef; color: #495057; font-weight: 600;">{{{{ date }}}}</td>
                        </tr>
                        {{% if deal_type %}}
                        <tr>
                            <td style="padding: 14px 16px; font-weight: 500; color: #212529;">Deal Type</td>
                            <td style="padding: 14px 16px; color: #495057; font-weight: 600;">
                                <span style="background-color: #e9ecef; padding: 4px 8px; border-radius: 12px; font-size: 12px; text-transform: uppercase;">{{{{ deal_type }}}}</span>
                            </td>
                        </tr>
                        {{% endif %}}
                    </table>
                    
                    <!-- Status Message -->
                    <div style="text-align: center; background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                        <p style="margin: 0; color: #495057; font-size: 16px; font-weight: 500;">
                            ✅ Deal {{{{ action }}}} completed successfully
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px; line-height: 1.5;">
                        This is an automated notification from <strong>Kotak Neo Trading Platform</strong>.<br>
                        Deal action completed successfully at {{{{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}}}
                    </p>
                    <p style="margin: 8px 0 0 0; color: #adb5bd; font-size: 12px;">
                        Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        try:
            from datetime import datetime
            template_data = {**deal_data, 'action': action, 'datetime': datetime}
            return template.render(**template_data)
        except Exception as e:
            # If template rendering fails, create a simple fallback
            logger.warning(f"Template rendering failed, using fallback: {e}")
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Deal {action.title()}: {deal_data.get('symbol', 'N/A')}</h2>
                <p><strong>User:</strong> {deal_data.get('username', 'N/A')}</p>
                <p><strong>Deal ID:</strong> {deal_data.get('deal_id', 'N/A')}</p>
                <p><strong>Quantity:</strong> {deal_data.get('quantity', 'N/A')}</p>
                <p><strong>Entry Price:</strong> ₹{deal_data.get('entry_price', 'N/A')}</p>
                <p>Deal {action} successfully.</p>
            </body>
            </html>
            """
    
    def _create_deal_text_template(self, deal_data: Dict[str, Any], action: str) -> str:
        """Create professional text template for deal notifications"""
        action_icons = {
            'created': '📊',
            'closed': '📉',
            'deleted': '🗑️'
        }
        
        icon = action_icons.get(action, '📊')
        invested_amount = deal_data.get('invested_amount', 0)
        current_value = deal_data.get('current_value', invested_amount)
        profit_loss = deal_data.get('profit_loss')
        
        # Calculate P&L if not provided
        if profit_loss is None and deal_data.get('exit_price') and deal_data.get('entry_price') and deal_data.get('quantity'):
            profit_loss = (float(deal_data['exit_price']) - float(deal_data['entry_price'])) * int(deal_data['quantity'])
        
        text = f"""
{icon} DEAL {action.upper()} NOTIFICATION
Kotak Neo Trading Platform

================================================
SYMBOL: {deal_data.get('symbol', 'N/A')}
DEAL ID: {deal_data.get('deal_id', 'N/A')}
================================================

DEAL INFORMATION:
------------------
User: {deal_data.get('username', 'N/A')}
Quantity: {deal_data.get('quantity', 'N/A')} shares
Entry Price: ₹{float(deal_data.get('entry_price', 0) or 0):.2f}"""
        
        if deal_data.get('target_price'):
            text += f"\nTarget Price: ₹{float(deal_data.get('target_price') or 0):.2f}"
            
        if deal_data.get('exit_price'):
            text += f"\nExit Price: ₹{float(deal_data.get('exit_price') or 0):.2f}"
        
        text += f"\nInvested Amount: ₹{float(invested_amount):.2f}"
        
        if current_value and current_value != invested_amount:
            text += f"\nCurrent Value: ₹{float(current_value):.2f}"
            
        # Show P&L for deal closure/deletion if available
        if profit_loss is not None and action in ['closed', 'deleted']:
            pnl_status = "PROFIT" if profit_loss >= 0 else "LOSS"
            pnl_sign = "+" if profit_loss >= 0 else ""
            text += f"\nP&L: {pnl_sign}₹{float(profit_loss):.2f} ({pnl_status})"
            
        text += f"\nDate: {deal_data.get('date', 'N/A')}"
        
        if deal_data.get('deal_type'):
            text += f"\nDeal Type: {deal_data.get('deal_type')}"
            
        text += f"""

STATUS: ✅ Deal {action} completed successfully

================================================
This is an automated notification from 
Kotak Neo Trading Platform.

Please do not reply to this email.
================================================
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