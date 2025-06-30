"""
Default Deals Sync Manager
Automatically syncs data from admin_trade_signals to default_deals table
"""

from app import app, db
from scripts.models import DefaultDeal
from scripts.models_etf import AdminTradeSignal
import logging

logger = logging.getLogger(__name__)

class DefaultDealsSync:
    """Manages synchronization between admin_trade_signals and default_deals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def sync_admin_signals_to_default_deals(self):
        """Sync all admin trade signals to default deals table"""
        try:
            with app.app_context():
                # Get all admin signals that don't have corresponding default deals
                admin_signals = db.session.query(AdminTradeSignal).outerjoin(DefaultDeal).filter(
                    DefaultDeal.admin_signal_id.is_(None)
                ).all()
                
                synced_count = 0
                for signal in admin_signals:
                    # Create new default deal from admin signal
                    default_deal = DefaultDeal(
                        user_target_id=signal.user_target_id,
                        symbol=signal.symbol,
                        exchange=signal.exchange,
                        position_type=signal.position_type,
                        quantity=signal.quantity,
                        entry_price=signal.entry_price,
                        current_price=signal.current_price,
                        price_change_percent=signal.price_change_percent,
                        investment_amount=signal.investment_amount,
                        target_price=signal.target_price,
                        total_value=signal.total_value,
                        target_pnl_ratio=signal.target_pnl_ratio,
                        pnl=signal.pnl,
                        entry_date=signal.entry_date,
                        exit_date=signal.exit_date,
                        profit_ratio=signal.profit_ratio,
                        profit_price=signal.profit_price,
                        intrinsic_value=signal.intrinsic_value,
                        intrinsic_price=signal.intrinsic_price,
                        notes=signal.notes,
                        quantity_traded=signal.quantity_traded,
                        seven_day_change=signal.seven_day_change,
                        change_amount=signal.change_amount,
                        signal_strength=signal.signal_strength,
                        admin_signal_id=signal.id
                    )
                    
                    db.session.add(default_deal)
                    synced_count += 1
                
                db.session.commit()
                self.logger.info(f"Synced {synced_count} admin signals to default deals")
                return synced_count
                
        except Exception as e:
            self.logger.error(f"Error syncing admin signals to default deals: {str(e)}")
            db.session.rollback()
            return 0
    
    def update_default_deal_from_admin_signal(self, admin_signal_id):
        """Update specific default deal when admin signal is updated"""
        try:
            with app.app_context():
                admin_signal = AdminTradeSignal.query.get(admin_signal_id)
                if not admin_signal:
                    return False
                
                default_deal = DefaultDeal.query.filter_by(admin_signal_id=admin_signal_id).first()
                if not default_deal:
                    # Create new default deal if doesn't exist
                    self.sync_admin_signals_to_default_deals()
                    return True
                
                # Update existing default deal
                default_deal.user_target_id = admin_signal.user_target_id
                default_deal.symbol = admin_signal.symbol
                default_deal.exchange = admin_signal.exchange
                default_deal.position_type = admin_signal.position_type
                default_deal.quantity = admin_signal.quantity
                default_deal.entry_price = admin_signal.entry_price
                default_deal.current_price = admin_signal.current_price
                default_deal.price_change_percent = admin_signal.price_change_percent
                default_deal.investment_amount = admin_signal.investment_amount
                default_deal.target_price = admin_signal.target_price
                default_deal.total_value = admin_signal.total_value
                default_deal.target_pnl_ratio = admin_signal.target_pnl_ratio
                default_deal.pnl = admin_signal.pnl
                default_deal.entry_date = admin_signal.entry_date
                default_deal.exit_date = admin_signal.exit_date
                default_deal.profit_ratio = admin_signal.profit_ratio
                default_deal.profit_price = admin_signal.profit_price
                default_deal.intrinsic_value = admin_signal.intrinsic_value
                default_deal.intrinsic_price = admin_signal.intrinsic_price
                default_deal.notes = admin_signal.notes
                default_deal.quantity_traded = admin_signal.quantity_traded
                default_deal.seven_day_change = admin_signal.seven_day_change
                default_deal.change_amount = admin_signal.change_amount
                default_deal.signal_strength = admin_signal.signal_strength
                
                db.session.commit()
                self.logger.info(f"Updated default deal for admin signal {admin_signal_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating default deal: {str(e)}")
            db.session.rollback()
            return False
    
    def get_all_default_deals(self):
        """Get all default deals with admin signal data"""
        try:
            with app.app_context():
                deals = db.session.query(DefaultDeal).join(
                    AdminTradeSignal, DefaultDeal.admin_signal_id == AdminTradeSignal.id, isouter=True
                ).all()
                
                return [self._deal_to_dict(deal) for deal in deals]
                
        except Exception as e:
            self.logger.error(f"Error getting default deals: {str(e)}")
            return []
    
    def _deal_to_dict(self, deal):
        """Convert default deal to dictionary"""
        return {
            'id': deal.id,
            'user_target_id': deal.user_target_id,
            'symbol': deal.symbol,
            'exchange': deal.exchange,
            'position_type': deal.position_type,
            'quantity': deal.quantity,
            'entry_price': float(deal.entry_price) if deal.entry_price else 0,
            'current_price': float(deal.current_price) if deal.current_price else 0,
            'price_change_percent': float(deal.price_change_percent) if deal.price_change_percent else 0,
            'investment_amount': float(deal.investment_amount) if deal.investment_amount else 0,
            'target_price': float(deal.target_price) if deal.target_price else 0,
            'total_value': float(deal.total_value) if deal.total_value else 0,
            'target_pnl_ratio': float(deal.target_pnl_ratio) if deal.target_pnl_ratio else 0,
            'pnl': float(deal.pnl) if deal.pnl else 0,
            'entry_date': deal.entry_date.isoformat() if deal.entry_date else None,
            'exit_date': deal.exit_date.isoformat() if deal.exit_date else None,
            'profit_ratio': float(deal.profit_ratio) if deal.profit_ratio else 0,
            'profit_price': float(deal.profit_price) if deal.profit_price else 0,
            'intrinsic_value': float(deal.intrinsic_value) if deal.intrinsic_value else 0,
            'intrinsic_price': float(deal.intrinsic_price) if deal.intrinsic_price else 0,
            'notes': deal.notes,
            'quantity_traded': deal.quantity_traded,
            'seven_day_change': float(deal.seven_day_change) if deal.seven_day_change else 0,
            'change_amount': float(deal.change_amount) if deal.change_amount else 0,
            'signal_strength': deal.signal_strength,
            'created_at': deal.created_at.isoformat() if deal.created_at else None,
            'updated_at': deal.updated_at.isoformat() if deal.updated_at else None,
            'admin_signal_id': deal.admin_signal_id
        }


# Global sync manager instance
sync_manager = DefaultDealsSync()

def auto_sync_on_admin_signal_change(admin_signal_id):
    """Automatically sync when admin signal changes"""
    return sync_manager.update_default_deal_from_admin_signal(admin_signal_id)

def get_default_deals_data():
    """Get all default deals data for API"""
    return sync_manager.get_all_default_deals()

def sync_all_admin_signals():
    """Sync all admin signals to default deals"""
    return sync_manager.sync_admin_signals_to_default_deals()