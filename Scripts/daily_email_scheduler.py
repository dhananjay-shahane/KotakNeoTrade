"""
Daily Email Scheduler for Trading Signal Changes
Sends daily summary emails to subscribed users about trading signal changes
"""
import os
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config.database_config import get_db_dict_connection

logger = logging.getLogger(__name__)

class DailyEmailScheduler:
    """Handles daily email notifications for subscribed users"""
    
    def __init__(self):
        self.email_service = None
        try:
            from api.email_service import EmailService
            self.email_service = EmailService()
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
    
    def get_subscribed_users(self) -> List[Dict[str, Any]]:
        """Get all users who have subscribed to daily email notifications"""
        try:
            conn = get_db_dict_connection()
            if not conn:
                logger.error("No database connection available")
                return []
            
            with conn.cursor() as cursor:
                # Get users with daily subscription enabled
                cursor.execute("""
                    SELECT u.username, u.email, ues.send_time, ues.subscription 
                    FROM external_users u
                    JOIN user_email_settings ues ON u.username = ues.username
                    WHERE ues.subscription = TRUE 
                    AND u.email IS NOT NULL 
                    AND u.email != ''
                """)
                
                users = cursor.fetchall()
                logger.info(f"Found {len(users)} subscribed users for daily emails")
                # Convert tuples to dictionaries for type compatibility
                return [{'username': u[0], 'email': u[1], 'send_time': u[2], 'subscription': u[3]} for u in users]
                
        except Exception as e:
            logger.error(f"Error getting subscribed users: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_daily_trading_changes(self) -> List[Dict[str, Any]]:
        """Get trading signal changes from the last 24 hours"""
        try:
            conn = get_db_dict_connection()
            if not conn:
                logger.error("No database connection available")
                return []
            
            with conn.cursor() as cursor:
                # Get signals created or updated in the last 24 hours
                yesterday = datetime.now() - timedelta(days=1)
                
                cursor.execute("""
                    SELECT 
                        symbol,
                        signal_type as action,
                        entry_price,
                        target_price,
                        stop_loss,
                        quantity,
                        status,
                        created_at,
                        updated_at
                    FROM admin_trade_signals 
                    WHERE created_at >= %s OR updated_at >= %s
                    ORDER BY created_at DESC
                """, (yesterday, yesterday))
                
                changes = cursor.fetchall()
                logger.info(f"Found {len(changes)} trading signal changes in last 24 hours")
                # Convert tuples to dictionaries for type compatibility
                return [{
                    'symbol': c[0], 'action': c[1], 'entry_price': c[2], 
                    'target_price': c[3], 'stop_loss': c[4], 'quantity': c[5],
                    'status': c[6], 'created_at': c[7], 'updated_at': c[8]
                } for c in changes]
                
        except Exception as e:
            logger.error(f"Error getting daily trading changes: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def send_daily_summary_email(self, user_email: str, username: str, changes: List[Dict[str, Any]]) -> bool:
        """Send daily summary email to a user"""
        try:
            if not self.email_service:
                logger.error("Email service not available")
                return False
            
            # Prepare email data
            email_data = {
                'username': username,
                'date': datetime.now().strftime('%d %B %Y'),
                'total_changes': len(changes),
                'changes': changes[:10]  # Limit to 10 most recent changes
            }
            
            # Send using the email service
            return self.email_service.send_daily_trading_changes_email(user_email, email_data)
            
        except Exception as e:
            logger.error(f"Error sending daily summary email to {user_email}: {e}")
            return False
    
    def run_daily_email_job(self):
        """Main job function that runs daily to send emails"""
        try:
            logger.info("Starting daily email job...")
            
            # Get subscribed users
            subscribed_users = self.get_subscribed_users()
            if not subscribed_users:
                logger.info("No subscribed users found, skipping daily emails")
                return
            
            # Get daily trading changes
            changes = self.get_daily_trading_changes()
            if not changes:
                logger.info("No trading signal changes in last 24 hours, skipping daily emails")
                return
            
            # Send emails to all subscribed users
            sent_count = 0
            failed_count = 0
            
            for user in subscribed_users:
                username = user['username']
                user_email = user['email']
                send_time = user.get('send_time', '09:00')
                
                try:
                    email_sent = self.send_daily_summary_email(user_email, username, changes)
                    if email_sent:
                        sent_count += 1
                        logger.info(f"✅ Daily email sent to {user_email}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Failed to send daily email to {user_email}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error sending daily email to {user_email}: {e}")
            
            logger.info(f"Daily email job completed: {sent_count} sent, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Error in daily email job: {e}")
    
    def setup_scheduler(self):
        """Setup daily email scheduler"""
        try:
            # Schedule daily emails at 9:00 AM (can be customized per user later)
            schedule.every().day.at("09:00").do(self.run_daily_email_job)
            logger.info("✅ Daily email scheduler configured for 9:00 AM")
            
            # Also schedule at 6:00 PM for users who prefer evening updates
            schedule.every().day.at("18:00").do(self.run_daily_email_job)
            logger.info("✅ Daily email scheduler configured for 6:00 PM")
            
        except Exception as e:
            logger.error(f"Error setting up scheduler: {e}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logger.info("Starting daily email scheduler...")
        self.setup_scheduler()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying


def start_daily_email_scheduler():
    """Start the daily email scheduler in background"""
    try:
        scheduler = DailyEmailScheduler()
        scheduler.run_scheduler()
    except Exception as e:
        logger.error(f"Failed to start daily email scheduler: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start scheduler
    start_daily_email_scheduler()