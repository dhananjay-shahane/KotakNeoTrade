#!/usr/bin/env python3
"""
Sync Default Deals - Synchronize admin_trade_signals to default_deals table
Run this script to populate default_deals with all admin_trade_signals data
"""

from app import app, db
from scripts.models import DefaultDeal, User
from scripts.models_etf import AdminTradeSignal
from sqlalchemy import text, event
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_admin_signals_to_default_deals():
    """Sync all admin trade signals to default deals table"""
    try:
        with app.app_context():
            logger.info("Starting sync from admin_trade_signals to default_deals...")

            # Get all admin trade signals using raw SQL to avoid model issues
            from sqlalchemy import text
            
            # Query admin_trade_signals with actual column names from CSV import
            result = db.session.execute(text("""
                SELECT id, etf, symbol, thirty, dh, date, pos, qty, ep, cmp, chan, 
                       inv, tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at
                FROM admin_trade_signals 
                ORDER BY created_at DESC
            """))
            
            admin_signals = result.fetchall()
            logger.info(f"Found {len(admin_signals)} admin trade signals to sync")

            synced_count = 0
            for signal in admin_signals:
                try:
                    # Check if default deal already exists for this admin signal
                    existing_deal = DefaultDeal.query.filter_by(admin_signal_id=signal.id).first()

                    if existing_deal:
                        # Update existing deal with CSV column mapping
                        existing_deal.symbol = signal.symbol
                        existing_deal.etf_name = signal.etf
                        existing_deal.exchange = 'NSE'  # Default since not in CSV
                        existing_deal.position_type = 'BUY' if signal.pos > 0 else 'SELL'
                        existing_deal.quantity = signal.qty
                        existing_deal.entry_price = signal.ep
                        existing_deal.current_price = signal.cmp
                        # Handle percentage change - remove % sign and convert to decimal
                        chan_value = signal.chan
                        if isinstance(chan_value, str) and '%' in chan_value:
                            chan_value = chan_value.replace('%', '')
                        existing_deal.price_change_percent = float(chan_value) if chan_value else 0.0
                        existing_deal.investment_amount = signal.inv
                        existing_deal.target_price = signal.tp
                        existing_deal.total_value = signal.tva
                        existing_deal.target_pnl_ratio = signal.tpr
                        existing_deal.pnl = signal.pl
                        existing_deal.entry_date = signal.date
                        existing_deal.expiry_date = signal.exp
                        existing_deal.profit_ratio = signal.pr
                        existing_deal.profit_price = signal.pp
                        existing_deal.intrinsic_value = signal.iv
                        existing_deal.intrinsic_price = signal.ip
                        existing_deal.notes = signal.nt
                        existing_deal.quantity_traded = signal.qt
                        existing_deal.seven_day_change = signal.seven
                        existing_deal.change_amount = signal.ch
                        existing_deal.profit_ratio = signal.pnl_percentage
                        existing_deal.profit_price = signal.current_price
                        existing_deal.intrinsic_value = signal.investment_amount
                        existing_deal.intrinsic_price = signal.entry_price
                        existing_deal.notes = signal.signal_description or signal.signal_title
                        existing_deal.quantity_traded = signal.quantity
                        existing_deal.seven_day_change = signal.change_percent
                        existing_deal.change_amount = signal.pnl
                        existing_deal.signal_strength = signal.status
                        logger.info(f"Updated existing default deal for admin signal {signal.id}")
                    else:
                        # Create new default deal with CSV column mapping
                        default_deal = DefaultDeal()
                        default_deal.user_target_id = str(signal.id)  # Use signal ID as target
                        default_deal.symbol = signal.symbol
                        default_deal.exchange = 'NSE'  # Default since not in CSV
                        default_deal.position_type = 'BUY' if signal.pos > 0 else 'SELL'
                        default_deal.quantity = signal.qty
                        default_deal.entry_price = signal.ep
                        default_deal.current_price = signal.cmp
                        # Handle percentage change - remove % sign and convert to decimal
                        chan_value = signal.chan
                        if isinstance(chan_value, str) and '%' in chan_value:
                            chan_value = chan_value.replace('%', '')
                        default_deal.price_change_percent = float(chan_value) if chan_value else 0.0
                        default_deal.investment_amount = signal.inv
                        default_deal.target_price = signal.tp
                        default_deal.total_value = signal.tva
                        default_deal.target_pnl_ratio = signal.tpr
                        default_deal.pnl = signal.pl
                        default_deal.entry_date = signal.date
                        default_deal.profit_ratio = signal.pr
                        default_deal.profit_price = signal.pp
                        default_deal.intrinsic_value = signal.iv
                        default_deal.intrinsic_price = signal.ip
                        default_deal.notes = signal.nt
                        default_deal.quantity_traded = signal.qt
                        default_deal.seven_day_change = signal.seven
                        default_deal.change_amount = signal.ch
                        default_deal.admin_signal_id = signal.id
                        db.session.add(default_deal)
                        logger.info(f"Created new default deal for admin signal {signal.id}")

                    synced_count += 1

                except Exception as e:
                    logger.error(f"Error syncing signal {signal.id}: {str(e)}")
                    continue

            db.session.commit()
            logger.info(f"Successfully synced {synced_count} admin signals to default deals")
            return synced_count

    except Exception as e:
        logger.error(f"Error syncing admin signals to default deals: {str(e)}")
        db.session.rollback()
        return 0

def update_default_deal_from_admin_signal_data(default_deal, admin_signal):
    """Update default deal with latest admin signal data"""
    default_deal.user_target_id = None  # Set to None since target_user_id doesn't exist in schema
    default_deal.symbol = admin_signal.symbol
    default_deal.exchange = admin_signal.exchange or 'NSE'
    default_deal.position_type = admin_signal.signal_type or 'BUY'
    default_deal.quantity = admin_signal.quantity or 0
    default_deal.entry_price = admin_signal.entry_price or 0.0
    default_deal.current_price = admin_signal.current_price or 0.0
    default_deal.price_change_percent = admin_signal.change_percent or 0.0
    default_deal.investment_amount = admin_signal.investment_amount or 0.0
    default_deal.target_price = admin_signal.target_price or 0.0
    default_deal.total_value = admin_signal.current_value or 0.0
    default_deal.target_pnl_ratio = admin_signal.pnl_percentage or 0.0
    default_deal.pnl = admin_signal.pnl or 0.0
    default_deal.entry_date = admin_signal.signal_date
    default_deal.profit_ratio = admin_signal.pnl_percentage or 0.0
    default_deal.profit_price = admin_signal.current_price or 0.0
    default_deal.intrinsic_value = admin_signal.investment_amount or 0.0
    default_deal.intrinsic_price = admin_signal.entry_price or 0.0
    default_deal.notes = admin_signal.signal_description or admin_signal.signal_title or ''
    default_deal.quantity_traded = admin_signal.quantity or 0
    default_deal.seven_day_change = admin_signal.change_percent or 0.0
    default_deal.change_amount = admin_signal.pnl or 0.0
    default_deal.signal_strength = admin_signal.status or 'ACTIVE'

def update_default_deal_from_admin_signal(admin_signal_id):
    """Update specific default deal when admin signal is updated"""
    try:
        with app.app_context():
            # Use raw SQL to get admin signal data
            from sqlalchemy import text
            
            result = db.session.execute(text("""
                SELECT id, symbol, exchange, signal_type, 
                       entry_price, target_price, stop_loss, quantity,
                       signal_title, signal_description, notes, priority, status,
                       created_at, updated_at, signal_date, expiry_date,
                       current_price, change_percent, investment_amount,
                       current_value, pnl, pnl_percentage
                FROM admin_trade_signals 
                WHERE id = :signal_id
            """), {'signal_id': admin_signal_id})
            
            admin_signal = result.fetchone()
            if not admin_signal:
                logger.warning(f"Admin signal {admin_signal_id} not found")
                return False

            default_deal = DefaultDeal.query.filter_by(admin_signal_id=admin_signal_id).first()
            if not default_deal:
                # Create new default deal if doesn't exist
                logger.info(f"Creating new default deal for admin signal {admin_signal_id}")
                default_deal = DefaultDeal(
                    admin_signal_id=admin_signal_id,
                    user_target_id=None,
                    symbol=admin_signal.symbol,
                    exchange=admin_signal.exchange or 'NSE',
                    position_type=admin_signal.signal_type or 'BUY',
                    quantity=admin_signal.quantity or 0,
                    entry_price=admin_signal.entry_price or 0.0,
                    current_price=admin_signal.current_price or 0.0,
                    price_change_percent=admin_signal.change_percent or 0.0,
                    investment_amount=admin_signal.investment_amount or 0.0,
                    target_price=admin_signal.target_price or 0.0,
                    total_value=admin_signal.current_value or 0.0,
                    target_pnl_ratio=admin_signal.pnl_percentage or 0.0,
                    pnl=admin_signal.pnl or 0.0,
                    entry_date=admin_signal.signal_date,
                    profit_ratio=admin_signal.pnl_percentage or 0.0,
                    profit_price=admin_signal.current_price or 0.0,
                    intrinsic_value=admin_signal.investment_amount or 0.0,
                    intrinsic_price=admin_signal.entry_price or 0.0,
                    notes=admin_signal.signal_description or admin_signal.signal_title or '',
                    quantity_traded=admin_signal.quantity or 0,
                    seven_day_change=admin_signal.change_percent or 0.0,
                    change_amount=admin_signal.pnl or 0.0,
                    signal_strength=admin_signal.status or 'ACTIVE'
                )
                db.session.add(default_deal)
            else:
                # Update existing default deal
                update_default_deal_from_admin_signal_data(default_deal, admin_signal)

            db.session.commit()
            logger.info(f"Successfully updated default deal for admin signal {admin_signal_id}")
            return True

    except Exception as e:
        logger.error(f"Error updating default deal for admin signal {admin_signal_id}: {str(e)}")
        db.session.rollback()
        return False

# Set up automatic sync triggers
def setup_auto_sync_triggers():
    """Setup automatic sync triggers for admin_trade_signals changes"""

    @event.listens_for(AdminTradeSignal, 'after_insert')
    def auto_sync_on_insert(mapper, connection, target):
        """Automatically sync when new admin signal is inserted"""
        try:
            logger.info(f"Auto-sync triggered: New admin signal {target.id} created")
            update_default_deal_from_admin_signal(target.id)
        except Exception as e:
            logger.error(f"Error in auto-sync on insert: {str(e)}")

    @event.listens_for(AdminTradeSignal, 'after_update')
    def auto_sync_on_update(mapper, connection, target):
        """Automatically sync when admin signal is updated"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} updated")
            update_default_deal_from_admin_signal(target.id)
        except Exception as e:
            logger.error(f"Error in auto-sync on update: {str(e)}")

    @event.listens_for(AdminTradeSignal, 'after_delete')
    def auto_sync_on_delete(mapper, connection, target):
        """Remove corresponding default deal when admin signal is deleted"""
        try:
            logger.info(f"Auto-sync triggered: Admin signal {target.id} deleted")
            with app.app_context():
                default_deal = DefaultDeal.query.filter_by(admin_signal_id=target.id).first()
                if default_deal:
                    db.session.delete(default_deal)
                    db.session.commit()
                    logger.info(f"Successfully removed default deal for deleted admin signal {target.id}")
        except Exception as e:
            logger.error(f"Error in auto-sync on delete: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    # Get current user for default assignment
    current_user = None
    try:
        current_user = User.query.first()  # Get any existing user
    except:
        pass
    result = sync_admin_signals_to_default_deals()
    print(f"Synced {result} records from admin_trade_signals to default_deals")