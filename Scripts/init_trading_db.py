"""
Initialize trading database with new tables
"""
from app import app, db
from scripts.models import User
from scripts.models_etf import AdminTradeSignal, UserNotification, UserDeal, ETFPosition
import logging

logging.basicConfig(level=logging.INFO)

def init_database():
    """Initialize database with all tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()

            logging.info("✅ Database tables created successfully!")

            # Print table information
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            print("\n📊 Created Tables:")
            for table in sorted(tables):
                print(f"  - {table}")

            print(f"\n🎯 Total tables: {len(tables)}")

            # Check if we can query the tables
            try:
                users_count = User.query.count()
                signals_count = AdminTradeSignal.query.count()
                deals_count = UserDeal.query.count()
                notifications_count = UserNotification.query.count()

                print(f"\n📈 Current Data:")
                print(f"  - Users: {users_count}")
                print(f"  - Trade Signals: {signals_count}")
                print(f"  - User Deals: {deals_count}")
                print(f"  - Notifications: {notifications_count}")

            except Exception as e:
                logging.warning(f"Could not query tables: {e}")

            return True

    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False

def create_sample_data():
    """Create some sample data for testing"""
    try:
        with app.app_context():
            # Check if we already have data
            if User.query.count() > 0:
                logging.info("Database already has data, skipping sample data creation")
                return True

            # Create sample admin user
            admin_user = User(
                ucc="ADMIN001",
                mobile_number="9999999999",
                greeting_name="Admin User",
                user_id="admin001",
                client_code="ADMIN",
                is_active=True
            )

            # Create sample regular user
            regular_user = User(
                ucc="USER001",
                mobile_number="8888888888", 
                greeting_name="Test User",
                user_id="user001",
                client_code="USER",
                is_active=True
            )

            db.session.add(admin_user)
            db.session.add(regular_user)
            db.session.commit()

            logging.info("✅ Sample users created!")

            return True

    except Exception as e:
        db.session.rollback()
        logging.error(f"Sample data creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing Trading Database...")

    # Initialize database
    if init_database():
        print("✅ Database initialization completed!")
        print("📊 Available tables:")
        print("   - admin_trade_signals")
        print("   - user_notifications")
        print("   - user_deals")
        print("   - etf_positions")
        print("   - etf_signal_trades")
        print("   - etf_watchlist")

        # Create sample data
        create_sample_data()

        print("\n🎉 Setup complete! You can now:")
        print("1. Use the admin API to send trade signals")
        print("2. Users can create deals from signals")
        print("3. Import signals from CSV files")
        print("4. Track all deals in the database")

    else:
        print("❌ Database initialization failed!")