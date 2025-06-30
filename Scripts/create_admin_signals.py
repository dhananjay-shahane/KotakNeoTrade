
#!/usr/bin/env python3
"""
Create sample admin trade signals for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from Scripts.models import User
from Scripts.models_etf import AdminTradeSignal
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_signals():
    """Create sample admin trade signals"""
    with app.app_context():
        try:
            # Get users from database
            users = User.query.all()
            if len(users) < 2:
                print("❌ Need at least 2 users in database. Please login with at least 2 accounts first.")
                return False

            admin_user = users[0]  # First user as admin
            target_users = users[1:3] if len(users) > 2 else users[1:2]  # Next 1-2 users as targets

            print(f"🔧 Using admin user: {admin_user.ucc}")
            print(f"📊 Target users: {[u.ucc for u in target_users]}")

            # Sample ETF signals data
            signals_data = [
                {
                    'symbol': 'NIFTYBEES',
                    'trading_symbol': 'NIFTYBEES-EQ',
                    'signal_type': 'BUY',
                    'entry_price': 245.50,
                    'target_price': 260.00,
                    'stop_loss': 235.00,
                    'quantity': 100,
                    'signal_title': 'NIFTY ETF - Bullish Breakout',
                    'signal_description': 'Strong momentum with volume surge. Target 260.',
                    'priority': 'HIGH'
                },
                {
                    'symbol': 'BANKBEES',
                    'trading_symbol': 'BANKBEES-EQ', 
                    'signal_type': 'BUY',
                    'entry_price': 520.75,
                    'target_price': 545.00,
                    'stop_loss': 505.00,
                    'quantity': 50,
                    'signal_title': 'Bank ETF - Sector Rotation',
                    'signal_description': 'Banking sector showing strength. Good risk-reward.',
                    'priority': 'MEDIUM'
                },
                {
                    'symbol': 'GOLDSHARE',
                    'trading_symbol': 'GOLDSHARE-EQ',
                    'signal_type': 'SELL',
                    'entry_price': 4850.00,
                    'target_price': 4720.00,
                    'stop_loss': 4920.00,
                    'quantity': 10,
                    'signal_title': 'Gold ETF - Profit Booking',
                    'signal_description': 'Gold overbought, book profits on strength.',
                    'priority': 'MEDIUM'
                },
                {
                    'symbol': 'ITBEES',
                    'trading_symbol': 'ITBEES-EQ',
                    'signal_type': 'BUY',
                    'entry_price': 385.25,
                    'target_price': 405.00,
                    'stop_loss': 370.00,
                    'quantity': 75,
                    'signal_title': 'IT ETF - Tech Recovery',
                    'signal_description': 'IT sector bottoming out, good entry point.',
                    'priority': 'HIGH'
                },
                {
                    'symbol': 'PSUBNKBEES',
                    'trading_symbol': 'PSUBNKBEES-EQ',
                    'signal_type': 'BUY',
                    'entry_price': 15.80,
                    'target_price': 17.50,
                    'stop_loss': 14.90,
                    'quantity': 500,
                    'signal_title': 'PSU Bank ETF - Value Pick',
                    'signal_description': 'PSU banks undervalued, government push expected.',
                    'priority': 'MEDIUM'
                }
            ]

            created_signals = 0
            
            # Create signals for each target user
            for target_user in target_users:
                for signal_data in signals_data:
                    signal = AdminTradeSignal(
                        admin_user_id=admin_user.id,
                        target_user_id=target_user.id,
                        symbol=signal_data['symbol'],
                        trading_symbol=signal_data['trading_symbol'],
                        token=f"NSE_{signal_data['symbol']}",
                        exchange='NSE',
                        signal_type=signal_data['signal_type'],
                        entry_price=signal_data['entry_price'],
                        target_price=signal_data['target_price'],
                        stop_loss=signal_data['stop_loss'],
                        quantity=signal_data['quantity'],
                        signal_title=signal_data['signal_title'],
                        signal_description=signal_data['signal_description'],
                        priority=signal_data['priority'],
                        status='ACTIVE',
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=30)
                    )
                    
                    db.session.add(signal)
                    created_signals += 1

            # Commit all signals
            db.session.commit()
            
            print(f"✅ Successfully created {created_signals} admin trade signals")
            print(f"📊 Signals created for {len(target_users)} target users")
            print(f"🚀 ETF Signals page will now show real-time data!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating admin signals: {e}")
            return False

if __name__ == "__main__":
    print("🏗️ Creating admin trade signals...")
    success = create_admin_signals()
    if success:
        print("\n🎉 Admin signals created successfully!")
        print("📈 Visit the ETF Signals page to see real-time data")
    else:
        print("\n❌ Failed to create admin signals")
