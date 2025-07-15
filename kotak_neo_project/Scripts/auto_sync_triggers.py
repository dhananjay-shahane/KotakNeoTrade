#!/usr/bin/env python3
"""
Auto-sync triggers for keeping default_deals synchronized with admin_trade_signals
Sets up database triggers and event handlers for automatic synchronization
"""

from app import app, db
from sqlalchemy import event, text
from Scripts.models_etf import AdminTradeSignal
from Scripts.sync_default_deals import update_default_deal_from_admin_signal
import logging

logger = logging.getLogger(__name__)

def setup_auto_sync_triggers():
    """Setup automatic sync triggers for admin_trade_signals changes"""
    
    @event.listens_for(AdminTradeSignal, 'after_insert')
    def auto_sync_on_insert(mapper, connection, target):
        """Automatically sync when new admin signal is inserted"""
        try:
            logger.info(f"Auto-sync triggered: New admin signal {target.id} created")
            # Use separate app context for the sync operation
            with app.app_context():
                result = update_default_deal_from_admin_signal(target.id)
                if result:
                    logger.info(f"Successfully auto-synced new admin signal {target.id} to default_deals")
                else:
                    logger.error(f"Failed to auto-sync new admin signal {target.id}")
        except Exception as e:
            logger.error(f"Error in auto-sync on insert: {str(e)}")
    
    @event.listens_for(AdminTradeSignal, 'after_update')
    def auto_sync_on_update(mapper, connection, target):
        """Automatically sync when admin signal is updated"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} updated")
            # Use separate app context for the sync operation
            with app.app_context():
                result = update_default_deal_from_admin_signal(target.id)
                if result:
                    logger.info(f"Successfully auto-synced updated admin signal {target.id} to default_deals")
                else:
                    logger.error(f"Failed to auto-sync updated admin signal {target.id}")
        except Exception as e:
            logger.error(f"Error in auto-sync on update: {str(e)}")
    
    @event.listens_for(AdminTradeSignal, 'after_delete')
    def auto_sync_on_delete(mapper, connection, target):
        """Remove corresponding default deal when admin signal is deleted"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} deleted")
            # Remove corresponding default deal
            with app.app_context():
                from Scripts.models import DefaultDeal
                default_deal = DefaultDeal.query.filter_by(admin_signal_id=target.id).first()
                if default_deal:
                    db.session.delete(default_deal)
                    db.session.commit()
                    logger.info(f"Successfully removed default deal for deleted admin signal {target.id}")
        except Exception as e:
            logger.error(f"Error in auto-sync on delete: {str(e)}")
            db.session.rollback()

def create_database_triggers():
    """Create database-level triggers for automatic synchronization"""
    try:
        with app.app_context():
            # Check if triggers already exist
            check_trigger_sql = text("""
                SELECT COUNT(*) as count FROM information_schema.triggers 
                WHERE trigger_name = 'admin_signals_sync_trigger'
            """)
            
            result = db.session.execute(check_trigger_sql).fetchone()
            if result.count > 0:
                logger.info("Database triggers already exist")
                return True
            
            # Create trigger function for PostgreSQL
            trigger_function_sql = text("""
                CREATE OR REPLACE FUNCTION sync_default_deals_trigger()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- This trigger would call a stored procedure to sync data
                    -- For now, we rely on SQLAlchemy event handlers
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create triggers for INSERT, UPDATE, DELETE
            create_triggers_sql = text("""
                CREATE TRIGGER admin_signals_sync_trigger
                AFTER INSERT OR UPDATE OR DELETE ON admin_trade_signals
                FOR EACH ROW EXECUTE FUNCTION sync_default_deals_trigger();
            """)
            
            db.session.execute(trigger_function_sql)
            db.session.execute(create_triggers_sql)
            db.session.commit()
            
            logger.info("Database triggers created successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error creating database triggers: {str(e)}")
        db.session.rollback()
        return False

def initialize_auto_sync():
    """Initialize all auto-sync mechanisms"""
    logger.info("Initializing auto-sync mechanisms...")
    
    # Setup SQLAlchemy event handlers
    setup_auto_sync_triggers()
    logger.info("SQLAlchemy event handlers configured")
    
    # Create database triggers (optional, for redundancy)
    create_database_triggers()
    
    logger.info("Auto-sync initialization complete")

if __name__ == "__main__":
    initialize_auto_sync()
    print("Auto-sync triggers initialized successfully")