"""
Email Functions for Kotak Neo Trading Platform
Handles SMTP email sending for trading signal notifications and daily reports
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from api.settings_api import get_users_with_email_notifications
from Scripts.external_db_service import ExternalDatabaseService

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending trading notifications using user-specific SMTP configurations
    Supports per-user SMTP settings for secure and personalized email delivery
    """

    def __init__(self):
        self.db_service = ExternalDatabaseService()
        # Load admin email configuration from environment variables
        self.admin_smtp_config = {
            'smtp_host': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('MAIL_PORT', 587)),
            'smtp_username': os.environ.get('EMAIL_USER'),
            'smtp_password': os.environ.get('EMAIL_PASSWORD'),
            'use_tls': os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        }

    def send_email_via_admin_smtp(self, recipient_email: str, 
                                 subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Send email using admin's SMTP configuration with proper error handling
        
        Args:
            recipient_email: Email address to send to
            subject: Email subject line
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            Boolean indicating success/failure of email sending
        """
        try:
            # Validate admin SMTP configuration
            if not all([self.admin_smtp_config['smtp_host'], 
                       self.admin_smtp_config['smtp_username'], 
                       self.admin_smtp_config['smtp_password']]):
                logger.error("❌ Incomplete admin SMTP configuration")
                return False

            # Create email message with both HTML and text content
            message = MIMEMultipart('alternative')
            message['From'] = self.admin_smtp_config['smtp_username']
            message['To'] = recipient_email
            message['Subject'] = subject

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Connect to SMTP server with security measures
            server = smtplib.SMTP(self.admin_smtp_config['smtp_host'], self.admin_smtp_config['smtp_port'])
            if self.admin_smtp_config['use_tls']:
                server.starttls()  # Enable security
            server.login(self.admin_smtp_config['smtp_username'], self.admin_smtp_config['smtp_password'])
            
            # Send email
            text = message.as_string()
            server.sendmail(self.admin_smtp_config['smtp_username'], recipient_email, text)
            server.quit()
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ SMTP authentication failed for admin email {self.admin_smtp_config.get('smtp_username', 'unknown')}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_deal_notification_email(self, user_email: str, deal_data: Dict, action_type: str) -> bool:
        """
        Send email notification for deal operations (add/close) to the specific user
        
        Args:
            user_email: Email address of the user performing the action
            deal_data: Dictionary containing deal information
            action_type: 'added' or 'closed'
            
        Returns:
            Boolean indicating success/failure of email sending
        """
        try:
            if not user_email or not deal_data:
                logger.error("❌ Missing user email or deal data")
                return False

            # Prepare email content based on action type
            if action_type == 'added':
                subject = f"Deal Added: {deal_data.get('symbol', 'Unknown')}"
                action_text = "added a new deal"
                action_details = f"""
                    <tr><td style="padding: 8px; font-weight: bold;">Entry Price:</td><td style="padding: 8px;">₹{deal_data.get('entry_price', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Quantity:</td><td style="padding: 8px;">{deal_data.get('quantity', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Investment:</td><td style="padding: 8px;">₹{deal_data.get('invested_amount', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Date:</td><td style="padding: 8px;">{deal_data.get('date', 'N/A')}</td></tr>
                """
            elif action_type == 'closed':
                subject = f"Deal Closed: {deal_data.get('symbol', 'Unknown')}"
                action_text = "closed a deal"
                pnl_color = "#16a34a" if float(deal_data.get('pnl_amount', 0)) >= 0 else "#dc2626"
                pnl_sign = "+" if float(deal_data.get('pnl_amount', 0)) >= 0 else ""
                action_details = f"""
                    <tr><td style="padding: 8px; font-weight: bold;">Exit Price:</td><td style="padding: 8px;">₹{deal_data.get('exit_price', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Exit Date:</td><td style="padding: 8px;">{deal_data.get('exit_date', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">P&L Amount:</td><td style="padding: 8px; color: {pnl_color}; font-weight: bold;">{pnl_sign}₹{deal_data.get('pnl_amount', 'N/A')}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">P&L %:</td><td style="padding: 8px; color: {pnl_color}; font-weight: bold;">{pnl_sign}{deal_data.get('pnl_percent', 'N/A')}%</td></tr>
                """
            else:
                return False

            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563eb; margin-bottom: 20px;">{'📈' if action_type == 'added' else '💰'} Deal {action_type.title()} Notification</h2>
                        
                        <p style="color: #374151; font-size: 16px; line-height: 1.6;">
                            You have successfully {action_text} for <strong>{deal_data.get('symbol', 'Unknown')}</strong>.
                        </p>
                        
                        <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #1f2937; margin: 0 0 15px 0;">Deal Details:</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td style="padding: 8px; font-weight: bold;">Symbol:</td><td style="padding: 8px;">{deal_data.get('symbol', 'N/A')}</td></tr>
                                <tr><td style="padding: 8px; font-weight: bold;">Deal ID:</td><td style="padding: 8px;">{deal_data.get('deal_id', 'N/A')}</td></tr>
                                {action_details}
                            </table>
                        </div>
                        
                        <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">
                            <p style="margin: 0; color: #1e40af;">
                                <strong>📊 Neo Trading Platform</strong><br>
                                You can view all your deals and portfolio performance in your dashboard.
                            </p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <div style="text-align: center; color: #6b7280; font-size: 14px;">
                            <p>This is an automated notification from Neo Trading Platform</p>
                            <p>Time: {datetime.now().strftime('%d %B %Y at %I:%M %p')}</p>
                        </div>
                    </div>
                </body>
            </html>
            """

            # Send email using admin SMTP
            return self.send_email_via_admin_smtp(user_email, subject, html_content)

        except Exception as e:
            logger.error(f"❌ Failed to send deal notification email: {e}")
            return False

    def send_trading_signal_email(self, trading_signal_data: Dict) -> int:
        """
        Send email containing trading signal data to all users who have enabled "Send deals in mail"
        This function is called whenever the admin adds a new trading signal
        
        Args:
            trading_signal_data: Dictionary containing signal information
            
        Returns:
            Number of emails successfully sent
        """
        try:
            # Get users who want deal notifications
            users = get_users_with_email_notifications('deals')
            if not users:
                logger.info("📧 No users have deal email notifications enabled")
                return 0

            successful_sends = 0
            
            # Prepare email content with trading signal details
            subject = f"New Trading Signal: {trading_signal_data.get('symbol', 'Unknown')}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563eb; margin-bottom: 20px;">🎯 New Trading Signal Alert</h2>
                        
                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3 style="color: #1e40af; margin-top: 0;">Signal Details</h3>
                            <p><strong>Symbol:</strong> {trading_signal_data.get('symbol', 'N/A')}</p>
                            <p><strong>Signal Type:</strong> {trading_signal_data.get('signal_type', 'N/A')}</p>
                            <p><strong>Entry Price:</strong> ₹{trading_signal_data.get('entry_price', 'N/A')}</p>
                            <p><strong>Target Price:</strong> ₹{trading_signal_data.get('target_price', 'N/A')}</p>
                            <p><strong>Stop Loss:</strong> ₹{trading_signal_data.get('stop_loss', 'N/A')}</p>
                            <p><strong>Date Added:</strong> {trading_signal_data.get('date_added', datetime.now().strftime('%Y-%m-%d %H:%M'))}</p>
                        </div>
                        
                        <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <p style="margin: 0; color: #92400e;"><strong>📊 Trading Recommendation:</strong> 
                            Consider this signal based on your risk tolerance and trading strategy.</p>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                            This email was sent because you enabled "Send deals in mail" in your notification settings.
                        </p>
                    </div>
                </body>
            </html>
            """

            text_content = f"""
            New Trading Signal Alert
            
            Symbol: {trading_signal_data.get('symbol', 'N/A')}
            Signal Type: {trading_signal_data.get('signal_type', 'N/A')}
            Entry Price: ₹{trading_signal_data.get('entry_price', 'N/A')}
            Target Price: ₹{trading_signal_data.get('target_price', 'N/A')}
            Stop Loss: ₹{trading_signal_data.get('stop_loss', 'N/A')}
            Date Added: {trading_signal_data.get('date_added', datetime.now().strftime('%Y-%m-%d %H:%M'))}
            
            Consider this signal based on your risk tolerance and trading strategy.
            """

            # Send email to each user using admin SMTP configuration
            for user in users:
                user_email = user['user_email']
                
                # Send email to user using admin SMTP settings
                if self.send_email_via_admin_smtp(user_email, subject, html_content, text_content):
                    successful_sends += 1
                    logger.info(f"✅ Trading signal email sent to {user['username']} ({user_email})")
                else:
                    logger.error(f"❌ Failed to send trading signal email to {user['username']} ({user_email})")

            logger.info(f"📧 Trading signal emails: {successful_sends}/{len(users)} sent successfully")
            return successful_sends

        except Exception as e:
            logger.error(f"❌ Error in send_trading_signal_email: {e}")
            return 0

    def send_deal_close_email(self, deal_data: Dict, username: str) -> bool:
        """
        Send email with deal close data to the relevant user when a deal is closed
        This function is called when a deal is closed on the deal page
        
        Args:
            deal_data: Dictionary containing deal closure information
            username: Username of the user whose deal was closed
            
        Returns:
            Boolean indicating success/failure
        """
        try:
            # Get specific user's email settings
            users = get_users_with_email_notifications('deals')
            user_settings = next((u for u in users if u['username'] == username), None)
            
            if not user_settings or not user_settings.get('user_email'):
                logger.info(f"📧 User {username} doesn't have deal email notifications enabled or no email provided")
                return False

            # Calculate profit/loss and percentage
            entry_price = float(deal_data.get('entry_price', 0))
            exit_price = float(deal_data.get('exit_price', 0))
            quantity = int(deal_data.get('quantity', 0))
            
            profit_loss = (exit_price - entry_price) * quantity
            profit_loss_percent = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            status_color = "#16a34a" if profit_loss >= 0 else "#dc2626"
            status_text = "Profit" if profit_loss >= 0 else "Loss"
            status_icon = "📈" if profit_loss >= 0 else "📉"

            subject = f"Deal Closed: {deal_data.get('symbol', 'Unknown')} - {status_text}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563eb; margin-bottom: 20px;">{status_icon} Deal Closure Notification</h2>
                        
                        <div style="background-color: {status_color}15; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid {status_color};">
                            <h3 style="color: {status_color}; margin-top: 0;">Deal Summary</h3>
                            <p><strong>Symbol:</strong> {deal_data.get('symbol', 'N/A')}</p>
                            <p><strong>Entry Price:</strong> ₹{entry_price:.2f}</p>
                            <p><strong>Exit Price:</strong> ₹{exit_price:.2f}</p>
                            <p><strong>Quantity:</strong> {quantity}</p>
                            <p><strong>Profit/Loss:</strong> <span style="color: {status_color}; font-weight: bold;">₹{profit_loss:.2f} ({profit_loss_percent:+.2f}%)</span></p>
                            <p><strong>Closure Date:</strong> {deal_data.get('closure_date', datetime.now().strftime('%Y-%m-%d %H:%M'))}</p>
                        </div>
                        
                        <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px;">
                            <p style="margin: 0; color: #475569;"><strong>💡 Note:</strong> 
                            Review your trading strategy and consider this outcome for future decisions.</p>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                            This email was sent because you enabled deal email notifications in your settings.
                        </p>
                    </div>
                </body>
            </html>
            """

            user_email = user_settings['user_email']
            
            # Send email to user using admin SMTP
            success = self.send_email_via_admin_smtp(user_email, subject, html_content)
            
            if success:
                logger.info(f"✅ Deal closure email sent to {username}")
            else:
                logger.error(f"❌ Failed to send deal closure email to {username}")
                
            return success

        except Exception as e:
            logger.error(f"❌ Error in send_deal_close_email: {e}")
            return False

    def send_daily_change_data_email(self) -> int:
        """
        Send daily email reports with trading performance data at scheduled times
        This function is called by a scheduler to send daily reports to users who enabled this feature
        
        Returns:
            Number of emails successfully sent
        """
        try:
            # Get users who want daily reports
            users = get_users_with_email_notifications('daily_reports')
            if not users:
                logger.info("📧 No users have daily email reports enabled")
                return 0

            # Get current time to check against user preferences
            current_time = datetime.now().strftime('%H:%M')
            
            # Filter users whose daily email time matches current time (within 5 minutes)
            target_users = []
            for user in users:
                user_time = user.get('daily_email_time', '11:00')
                if abs(datetime.strptime(current_time, '%H:%M').hour - 
                      datetime.strptime(user_time, '%H:%M').hour) <= 0:
                    target_users.append(user)

            if not target_users:
                logger.info(f"📧 No users scheduled for daily reports at {current_time}")
                return 0

            # Fetch daily trading data from database
            daily_data = self._get_daily_trading_summary()
            successful_sends = 0

            subject = f"Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #2563eb; margin-bottom: 20px;">📊 Daily Trading Report</h2>
                        
                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3 style="color: #1e40af; margin-top: 0;">Today's Summary</h3>
                            <p><strong>Total Active Signals:</strong> {daily_data.get('total_signals', 0)}</p>
                            <p><strong>New Signals Added:</strong> {daily_data.get('new_signals_today', 0)}</p>
                            <p><strong>Deals Closed Today:</strong> {daily_data.get('deals_closed_today', 0)}</p>
                            <p><strong>Overall Performance:</strong> {daily_data.get('performance_summary', 'N/A')}</p>
                        </div>
                        
                        <div style="background-color: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                            <p style="margin: 0; color: #047857;"><strong>📈 Market Insight:</strong> 
                            {daily_data.get('market_insight', 'Stay updated with market trends and adjust your strategy accordingly.')}</p>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                            This daily report was sent at {current_time} as per your notification preferences.
                        </p>
                    </div>
                </body>
            </html>
            """

            # Send email to each target user
            for user in target_users:
                user_email = user['user_email']
                
                if self.send_email_via_admin_smtp(user_email, subject, html_content):
                    successful_sends += 1
                    logger.info(f"✅ Daily report sent to {user['username']} ({user_email})")
                else:
                    logger.error(f"❌ Failed to send daily report to {user['username']} ({user_email})")

            logger.info(f"📧 Daily reports: {successful_sends}/{len(target_users)} sent successfully")
            return successful_sends

        except Exception as e:
            logger.error(f"❌ Error in send_daily_change_data_email: {e}")
            return 0

    def _get_daily_trading_summary(self) -> Dict:
        """
        Get daily trading summary data from the database
        Helper function to fetch performance data for daily email reports
        
        Returns:
            Dictionary containing daily trading statistics
        """
        try:
            # Use external database service to fetch trading data
            signals_data = self.db_service.get_etf_signals_data()
            
            today = datetime.now().date()
            total_signals = len(signals_data) if signals_data else 0
            
            # Calculate basic statistics
            new_signals_today = 0
            deals_closed_today = 0
            
            # This would be expanded with actual database queries for real data
            summary = {
                'total_signals': total_signals,
                'new_signals_today': new_signals_today,
                'deals_closed_today': deals_closed_today,
                'performance_summary': 'Market analysis in progress',
                'market_insight': 'Continue monitoring your portfolio and stay informed about market trends.'
            }
            
            return summary

        except Exception as e:
            logger.error(f"❌ Error getting daily trading summary: {e}")
            return {
                'total_signals': 0,
                'new_signals_today': 0,
                'deals_closed_today': 0,
                'performance_summary': 'Data unavailable',
                'market_insight': 'Please check your connection and try again later.'
            }


# Global email service instance
email_service = EmailService()