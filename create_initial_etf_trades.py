
#!/usr/bin/env python3
"""
Script to create initial ETF signal trades for real-time tracking
Run this once to populate the database with ETF trades
"""

from app import app, db
from models import User
from models_etf import ETFSignalTrade
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ETF instruments to create trades for
ETF_INSTRUMENTS = [
    {'symbol': 'NIFTYBEES', 'name': 'Nippon India ETF Nifty BeES', 'token': '15068', 'entry_price': 230.0},
    {'symbol': 'GOLDBEES', 'name': 'Nippon India ETF Gold BeES', 'token': '1660', 'entry_price': 40.0},
    {'symbol': 'BANKBEES', 'name': 'Nippon India ETF Bank BeES', 'token': '34605', 'entry_price': 46.0},
    {'symbol': 'ITBEES', 'name': 'Nippon India ETF IT BeES', 'token': '1348', 'entry_price': 65.0},
    {'symbol': 'JUNIORBEES', 'name': 'Nippon India ETF Junior BeES', 'token': '15081', 'entry_price': 96.0},
    {'symbol': 'SILVERBEES', 'name': 'Nippon India ETF Silver BeES', 'token': '1659', 'entry_price': 94.0},
    {'symbol': 'LIQUIDBEES', 'name': 'Nippon India ETF Liquid BeES', 'token': '15060', 'entry_price': 1000.0},
    {'symbol': 'PSUBNKBEES', 'name': 'Nippon India ETF PSU Bank BeES', 'token': '34604', 'entry_price': 16.5},
    {'symbol': 'PVTBNKBEES', 'name': 'Nippon India ETF Pvt Bank BeES', 'token': '34603', 'entry_price': 20.0},
    {'symbol': 'PHARMABEES', 'name': 'Nippon India ETF Pharma BeES', 'token': '1347', 'entry_price': 73.0},
    {'symbol': 'ICICINIFTY', 'name': 'ICICI Prudential Nifty ETF', 'token': '1082', 'entry_price': 80.0},
    {'symbol': 'HDFCNIFTY', 'name': 'HDFC Nifty 50 ETF', 'token': '1073', 'entry_price': 87.0},
    {'symbol': 'UTINIFTY', 'name': 'UTI Nifty 50 ETF', 'token': '1066', 'entry_price': 92.0},
    {'symbol': 'LICNFNXT50', 'name': 'LIC MF Nifty Next 50 ETF', 'token': '1320', 'entry_price': 34.0},
    {'symbol': 'ICICIB22', 'name': 'ICICI Prudential Bharat 22 ETF', 'token': '1299', 'entry_price': 300.0},
    {'symbol': 'HDFCMFGETF', 'name': 'HDFC Gold ETF', 'token': '1310', 'entry_price': 57.5},
    {'symbol': 'KOTAKNIFTY', 'name': 'Kotak Nifty ETF', 'token': '1154', 'entry_price': 90.0},
    {'symbol': 'RELIANCE', 'name': 'Reliance Industries Ltd', 'token': '2885', 'entry_price': 2850.0},
    {'symbol': 'TCS', 'name': 'Tata Consultancy Services', 'token': '11536', 'entry_price': 4150.0},
    {'symbol': 'INFY', 'name': 'Infosys Limited', 'token': '1594', 'entry_price': 1850.0},
]

def create_initial_etf_trades():
    """Create initial ETF trades for all users"""
    with app.app_context():
        try:
            # Get all users
            users = User.query.filter_by(is_active=True).all()
            if not users:
                logger.error("No active users found")
                return

            logger.info(f"Creating ETF trades for {len(users)} users")

            # Clear existing ETF trades
            ETFSignalTrade.query.delete()
            db.session.commit()
            
            trades_created = 0

            for user in users:
                logger.info(f"Creating trades for user: {user.ucc or user.id}")
                
                for i, etf in enumerate(ETF_INSTRUMENTS):
                    try:
                        # Determine signal type (alternate BUY/SELL)
                        signal_type = 'BUY' if i % 2 == 0 else 'SELL'
                        
                        # Calculate investment details
                        quantity = 50 + (i * 10)  # Varying quantities
                        entry_price = etf['entry_price']
                        invested_amount = entry_price * quantity
                        
                        # Set target and stop loss
                        if signal_type == 'BUY':
                            target_price = entry_price * 1.10  # 10% target
                            stop_loss = entry_price * 0.95     # 5% stop loss
                        else:
                            target_price = entry_price * 0.90  # 10% target (for short)
                            stop_loss = entry_price * 1.05     # 5% stop loss (for short)

                        # Create ETF signal trade
                        trade = ETFSignalTrade(
                            user_id=user.id,
                            assigned_by_user_id=users[0].id,  # First user as admin
                            symbol=etf['symbol'],
                            etf_name=etf['name'],
                            trading_symbol=f"{etf['symbol']}-EQ",
                            token=etf['token'],
                            exchange='NSE',
                            signal_type=signal_type,
                            quantity=quantity,
                            entry_price=entry_price,
                            current_price=entry_price,  # Start with entry price
                            target_price=target_price,
                            stop_loss=stop_loss,
                            invested_amount=invested_amount,
                            current_value=invested_amount,
                            pnl_amount=0.0,
                            pnl_percent=0.0,
                            trade_title=f"{signal_type} Signal - {etf['symbol']}",
                            trade_description=f"ETF {signal_type} signal for {etf['name']}",
                            priority='MEDIUM',
                            status='ACTIVE',
                            position_type='LONG' if signal_type == 'BUY' else 'SHORT',
                            entry_date=datetime.utcnow(),
                            last_price_update=datetime.utcnow()
                        )

                        db.session.add(trade)
                        trades_created += 1

                    except Exception as e:
                        logger.error(f"Error creating trade for {etf['symbol']}: {str(e)}")
                        continue

            # Commit all trades
            db.session.commit()
            logger.info(f"✅ Successfully created {trades_created} ETF trades")

            return trades_created

        except Exception as e:
            logger.error(f"Error creating initial ETF trades: {str(e)}")
            db.session.rollback()
            return 0

if __name__ == '__main__':
    count = create_initial_etf_trades()
    print(f"Created {count} initial ETF trades for real-time tracking")
