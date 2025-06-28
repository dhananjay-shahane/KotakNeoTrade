#!/usr/bin/env python3
"""
Sync Default Deals - Synchronize admin_trade_signals to default_deals table
Run this script to populate default_deals with all admin_trade_signals data
"""

from app import app, db
from Scripts.models import DefaultDeal
from Scripts.models_etf import AdminTradeSignal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_admin_signals_to_default_deals():
    """Sync all admin trade signals to default deals table"""
    try:
        with app.app_context():
            logger.info("Starting sync from admin_trade_signals to default_deals...")
            
            # Clear existing default deals to avoid duplicates
            db.session.execute(text("DELETE FROM default_deals"))
            
            # Get all admin trade signals
            admin_signals = AdminTradeSignal.query.all()
            logger.info(f"Found {len(admin_signals)} admin trade signals to sync")
            
            synced_count = 0
            for signal in admin_signals:
                try:
                    # Create new default deal from admin signal
                    default_deal = DefaultDeal(
                        user_target_id=str(signal.target_user_id) if signal.target_user_id else None,
                        symbol=signal.symbol,
                        exchange=signal.exchange or 'NSE',
                        position_type=signal.signal_type or 'BUY',
                        quantity=signal.quantity,
                        entry_price=signal.entry_price,
                        current_price=signal.current_price,
                        price_change_percent=signal.change_percent,
                        investment_amount=signal.investment_amount,
                        target_price=signal.target_price,
                        total_value=signal.current_value,
                        target_pnl_ratio=signal.pnl_percentage,
                        pnl=signal.pnl,
                        entry_date=signal.signal_date,
                        exit_date=None,
                        profit_ratio=signal.pnl_percentage,
                        profit_price=signal.current_price,
                        intrinsic_value=signal.investment_amount,
                        intrinsic_price=signal.entry_price,
                        notes=signal.signal_description or signal.signal_title,
                        quantity_traded=signal.quantity,
                        seven_day_change=signal.change_percent,
                        change_amount=signal.pnl,
                        signal_strength=signal.status,
                        admin_signal_id=signal.id
                    )
                    
                    db.session.add(default_deal)
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

def update_default_deal_from_admin_signal(admin_signal_id):
    """Update specific default deal when admin signal is updated"""
    try:
        with app.app_context():
            admin_signal = AdminTradeSignal.query.get(admin_signal_id)
            if not admin_signal:
                logger.warning(f"Admin signal {admin_signal_id} not found")
                return False
            
            default_deal = DefaultDeal.query.filter_by(admin_signal_id=admin_signal_id).first()
            if not default_deal:
                # Create new default deal if doesn't exist
                logger.info(f"Creating new default deal for admin signal {admin_signal_id}")
                default_deal = DefaultDeal(admin_signal_id=admin_signal_id)
                db.session.add(default_deal)
            
            # Update default deal with latest admin signal data
            default_deal.user_target_id = str(admin_signal.target_user_id) if admin_signal.target_user_id else None
            default_deal.symbol = admin_signal.symbol
            default_deal.exchange = admin_signal.exchange or 'NSE'
            default_deal.position_type = admin_signal.signal_type or 'BUY'
            default_deal.quantity = admin_signal.quantity
            default_deal.entry_price = admin_signal.entry_price
            default_deal.current_price = admin_signal.current_price
            default_deal.price_change_percent = admin_signal.change_percent
            default_deal.investment_amount = admin_signal.investment_amount
            default_deal.target_price = admin_signal.target_price
            default_deal.total_value = admin_signal.current_value
            default_deal.target_pnl_ratio = admin_signal.pnl_percentage
            default_deal.pnl = admin_signal.pnl
            default_deal.entry_date = admin_signal.signal_date
            default_deal.profit_ratio = admin_signal.pnl_percentage
            default_deal.profit_price = admin_signal.current_price
            default_deal.intrinsic_value = admin_signal.investment_amount
            default_deal.intrinsic_price = admin_signal.entry_price
            default_deal.notes = admin_signal.signal_description or admin_signal.signal_title
            default_deal.quantity_traded = admin_signal.quantity
            default_deal.seven_day_change = admin_signal.change_percent
            default_deal.change_amount = admin_signal.pnl
            default_deal.signal_strength = admin_signal.status
            
            db.session.commit()
            logger.info(f"Updated default deal for admin signal {admin_signal_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error updating default deal: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    result = sync_admin_signals_to_default_deals()
    print(f"Synced {result} records from admin_trade_signals to default_deals")