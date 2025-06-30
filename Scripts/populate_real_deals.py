
"""
Script to populate real user deals from CSV data
"""
from app import app, db
from scripts.models import User
from scripts.models_etf import UserDeal
from scripts.csv_data_fetcher import CSVDataFetcher
from datetime import datetime, timedelta
import logging
import random

def populate_deals_from_csv():
    """Populate user deals from real CSV data"""
    with app.app_context():
        try:
            # Initialize CSV data fetcher
            csv_fetcher = CSVDataFetcher()
            
            # Get real positions data from CSV
            positions = csv_fetcher.fetch_positions_data()
            
            if not positions:
                logging.info("No positions found in CSV data")
                return
            
            # Get or create default user
            user = User.query.filter_by(ucc='DEFAULT_USER').first()
            if not user:
                user = User(
                    ucc='DEFAULT_USER',
                    mobile_number='0000000000',
                    greeting_name='CSV User',
                    user_id='CSV_USER',
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
            
            # Clear existing deals for this user
            UserDeal.query.filter_by(user_id=user.id).delete()
            
            # Create deals from real CSV positions
            deals_created = 0
            for position in positions:
                try:
                    # Simulate entry date (1-30 days ago)
                    days_ago = random.randint(1, 30)
                    entry_date = datetime.now() - timedelta(days=days_ago)
                    
                    # Create deal from position
                    deal = UserDeal(
                        user_id=user.id,
                        symbol=position['symbol'],
                        trading_symbol=position['symbol'],
                        exchange='NSE',
                        position_type='LONG',
                        quantity=position['quantity'],
                        entry_price=position['avg_price'],
                        current_price=position['ltp'],
                        invested_amount=position['value'],
                        status='ACTIVE',
                        deal_type='CSV_IMPORT',
                        notes=f'Imported from CSV data - Current Value: ₹{position["current_value"]:.2f}',
                        tags='CSV_REAL_DATA',
                        entry_date=entry_date
                    )
                    
                    # Calculate P&L
                    deal.calculate_pnl()
                    
                    db.session.add(deal)
                    deals_created += 1
                    
                except Exception as e:
                    logging.error(f"Error creating deal for {position.get('symbol', 'Unknown')}: {str(e)}")
                    continue
            
            # Commit all deals
            db.session.commit()
            logging.info(f"Successfully created {deals_created} real deals from CSV data")
            
        except Exception as e:
            logging.error(f"Error populating deals from CSV: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    populate_deals_from_csv()
