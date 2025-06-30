#!/usr/bin/env python3
"""
Automatic Synchronization System for admin_trade_signals to default_deals
Creates real-time sync triggers and handlers for automatic data synchronization
"""

from app import app, db
from sqlalchemy import event, text
import logging

logger = logging.getLogger(__name__)

def create_database_trigger():
    """Create database-level trigger for automatic synchronization"""
    try:
        with app.app_context():
            # Create trigger function for PostgreSQL
            trigger_function = """
            CREATE OR REPLACE FUNCTION sync_admin_signals_to_default_deals()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Delete existing default deal if it exists
                DELETE FROM default_deals WHERE admin_signal_id = NEW.id;
                
                -- Insert new default deal with proper data mapping
                INSERT INTO default_deals (
                    user_target_id, symbol, exchange, position_type, quantity,
                    entry_price, current_price, price_change_percent,
                    investment_amount, target_price, total_value, target_pnl_ratio,
                    pnl, entry_date, profit_ratio, profit_price, intrinsic_value,
                    intrinsic_price, notes, quantity_traded, seven_day_change,
                    change_amount, admin_signal_id, created_at, updated_at
                ) VALUES (
                    CAST(NEW.id AS TEXT), -- user_target_id
                    NEW.symbol, -- symbol
                    'NSE', -- exchange (default)
                    CASE WHEN NEW.pos > 0 THEN 'BUY' ELSE 'SELL' END, -- position_type
                    NEW.qty, -- quantity
                    NEW.ep, -- entry_price
                    NEW.cmp, -- current_price
                    CASE 
                        WHEN NEW.chan IS NOT NULL AND NEW.chan != '' THEN
                            CAST(REPLACE(NEW.chan, '%', '') AS NUMERIC)
                        ELSE 0.0
                    END, -- price_change_percent
                    NEW.inv, -- investment_amount
                    NEW.tp, -- target_price
                    NEW.tva, -- total_value
                    CASE 
                        WHEN NEW.tpr IS NOT NULL AND NEW.tpr != '' AND NEW.tpr ~ '^[0-9.-]+$' THEN
                            CAST(NEW.tpr AS NUMERIC)
                        ELSE NULL
                    END, -- target_pnl_ratio
                    NEW.pl, -- pnl
                    NEW.date, -- entry_date
                    CASE 
                        WHEN NEW.pr IS NOT NULL AND NEW.pr != '' AND NEW.pr ~ '^[0-9.-]+$' THEN
                            CAST(NEW.pr AS NUMERIC)
                        ELSE NULL
                    END, -- profit_ratio
                    CASE 
                        WHEN NEW.pp IS NOT NULL AND NEW.pp != '' AND NEW.pp ~ '^[0-9.-]+$' THEN
                            CAST(NEW.pp AS NUMERIC)
                        ELSE NULL
                    END, -- profit_price
                    CASE 
                        WHEN NEW.iv IS NOT NULL AND NEW.iv != '' AND NEW.iv ~ '^[0-9.-]+$' THEN
                            CAST(NEW.iv AS NUMERIC)
                        ELSE NULL
                    END, -- intrinsic_value
                    CASE 
                        WHEN NEW.ip IS NOT NULL AND NEW.ip != '' AND NEW.ip ~ '^[0-9.-]+$' THEN
                            CAST(NEW.ip AS NUMERIC)
                        ELSE NULL
                    END, -- intrinsic_price
                    CASE 
                        WHEN NEW.nt IS NOT NULL THEN NEW.nt
                        ELSE 0
                    END, -- notes
                    NEW.qt, -- quantity_traded
                    CASE 
                        WHEN NEW.seven IS NOT NULL AND NEW.seven != '' AND NEW.seven ~ '^[0-9.-]+$' THEN
                            CAST(NEW.seven AS NUMERIC)
                        ELSE NULL
                    END, -- seven_day_change
                    CASE 
                        WHEN NEW.ch IS NOT NULL AND NEW.ch != '' AND NEW.ch ~ '^[0-9.-]+$' THEN
                            CAST(NEW.ch AS NUMERIC)
                        ELSE NULL
                    END, -- change_amount
                    NEW.id, -- admin_signal_id
                    CURRENT_TIMESTAMP, -- created_at
                    CURRENT_TIMESTAMP -- updated_at
                );
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # Execute trigger function creation
            db.session.execute(text(trigger_function))
            
            # Drop existing trigger if it exists
            drop_trigger = """
            DROP TRIGGER IF EXISTS auto_sync_admin_signals_trigger ON admin_trade_signals;
            """
            db.session.execute(text(drop_trigger))
            
            # Create trigger that fires on INSERT and UPDATE
            create_trigger = """
            CREATE TRIGGER auto_sync_admin_signals_trigger
                AFTER INSERT OR UPDATE ON admin_trade_signals
                FOR EACH ROW
                EXECUTE FUNCTION sync_admin_signals_to_default_deals();
            """
            db.session.execute(text(create_trigger))
            
            db.session.commit()
            logger.info("✓ Database trigger created successfully for automatic sync")
            return True
            
    except Exception as e:
        logger.error(f"Error creating database trigger: {str(e)}")
        db.session.rollback()
        return False

def setup_application_event_handlers():
    """Setup SQLAlchemy event handlers for admin_trade_signals changes"""
    from scripts.models_etf import AdminTradeSignal
    from scripts.models import DefaultDeal
    
    @event.listens_for(AdminTradeSignal, 'after_insert', propagate=True)
    def auto_sync_on_insert(mapper, connection, target):
        """Automatically sync when new admin signal is inserted"""
        try:
            logger.info(f"Auto-sync triggered: New admin signal {target.id} created")
            # The database trigger will handle the actual sync
            logger.info(f"Database trigger will sync admin signal {target.id} to default_deals")
        except Exception as e:
            logger.error(f"Error in auto-sync on insert: {str(e)}")
    
    @event.listens_for(AdminTradeSignal, 'after_update', propagate=True)
    def auto_sync_on_update(mapper, connection, target):
        """Automatically sync when admin signal is updated"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} updated")
            # The database trigger will handle the actual sync
            logger.info(f"Database trigger will sync updated admin signal {target.id} to default_deals")
        except Exception as e:
            logger.error(f"Error in auto-sync on update: {str(e)}")
    
    @event.listens_for(AdminTradeSignal, 'after_delete', propagate=True)
    def auto_sync_on_delete(mapper, connection, target):
        """Remove corresponding default deal when admin signal is deleted"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} deleted")
            # Delete corresponding default deal
            connection.execute(
                text("DELETE FROM default_deals WHERE admin_signal_id = :signal_id"),
                {"signal_id": target.id}
            )
            logger.info(f"Successfully removed default deal for deleted admin signal {target.id}")
        except Exception as e:
            logger.error(f"Error in auto-sync on delete: {str(e)}")

def initialize_auto_sync_system():
    """Initialize complete automatic synchronization system"""
    try:
        logger.info("Initializing automatic synchronization system...")
        
        # Step 1: Create database-level trigger
        trigger_success = create_database_trigger()
        
        # Step 2: Setup application event handlers
        setup_application_event_handlers()
        
        # Step 3: Perform initial sync of existing data
        from scripts.sync_default_deals import sync_admin_signals_to_default_deals
        initial_sync_count = sync_admin_signals_to_default_deals()
        
        logger.info(f"✓ Auto-sync system initialized successfully")
        logger.info(f"✓ Database trigger: {'Created' if trigger_success else 'Failed'}")
        logger.info(f"✓ Event handlers: Registered")
        logger.info(f"✓ Initial sync: {initial_sync_count} records")
        
        return {
            'success': True,
            'trigger_created': trigger_success,
            'event_handlers_registered': True,
            'initial_sync_count': initial_sync_count
        }
        
    except Exception as e:
        logger.error(f"Error initializing auto-sync system: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def test_auto_sync():
    """Test the automatic synchronization system"""
    try:
        logger.info("Testing automatic synchronization system...")
        
        # Count current records
        with app.app_context():
            admin_count = db.session.execute(text("SELECT COUNT(*) FROM admin_trade_signals")).scalar()
            default_count = db.session.execute(text("SELECT COUNT(*) FROM default_deals")).scalar()
            
            logger.info(f"Current counts - Admin signals: {admin_count}, Default deals: {default_count}")
            
            # Test by inserting a sample record
            test_insert = """
            INSERT INTO admin_trade_signals (
                etf, symbol, pos, qty, ep, cmp, chan, inv, tp, tva, pl, date
            ) VALUES (
                'TEST_ETF', 'TESTETF', 1, 100, 50.00, 52.00, '4.00%', 5000.00, 55.00, 5200.00, 200.00, '2025-06-28'
            ) RETURNING id;
            """
            
            result = db.session.execute(text(test_insert))
            test_id = result.scalar()
            db.session.commit()
            
            # Check if default deal was created automatically
            default_deal_exists = db.session.execute(
                text("SELECT COUNT(*) FROM default_deals WHERE admin_signal_id = :id"),
                {"id": test_id}
            ).scalar()
            
            # Clean up test record
            db.session.execute(text("DELETE FROM admin_trade_signals WHERE id = :id"), {"id": test_id})
            db.session.execute(text("DELETE FROM default_deals WHERE admin_signal_id = :id"), {"id": test_id})
            db.session.commit()
            
            test_success = default_deal_exists > 0
            logger.info(f"✓ Auto-sync test: {'PASSED' if test_success else 'FAILED'}")
            
            return test_success
            
    except Exception as e:
        logger.error(f"Error testing auto-sync: {str(e)}")
        return False

if __name__ == "__main__":
    result = initialize_auto_sync_system()
    print(f"Auto-sync system initialization: {result}")
    
    if result['success']:
        test_result = test_auto_sync()
        print(f"Auto-sync test: {'PASSED' if test_result else 'FAILED'}")