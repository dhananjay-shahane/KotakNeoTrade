"""
Dynamic User Deals Service
Provides services for managing user deals dynamically
"""
import logging
from Scripts.models import db, User
from Scripts.models_etf import UserDeal
from datetime import datetime
from typing import List, Dict, Any, Optional

class DynamicUserDealsService:
    """Service class for dynamic user deals operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_deals(self, user_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Get user deals with optional filters"""
        try:
            query = UserDeal.query.filter_by(user_id=user_id)
            
            if filters:
                if filters.get('symbol'):
                    query = query.filter(UserDeal.symbol.ilike(f"%{filters['symbol']}%"))
                if filters.get('status'):
                    query = query.filter(UserDeal.status == filters['status'].upper())
                if filters.get('deal_type'):
                    query = query.filter(UserDeal.deal_type == filters['deal_type'].upper())
            
            deals = query.order_by(UserDeal.created_at.desc()).all()
            return [deal.to_dict() for deal in deals]
            
        except Exception as e:
            self.logger.error(f"Error fetching user deals: {e}")
            return []
    
    def create_user_deal(self, user_id: int, deal_data: Dict) -> Optional[Dict]:
        """Create a new user deal"""
        try:
            deal = UserDeal(
                user_id=user_id,
                symbol=deal_data.get('symbol'),
                quantity=deal_data.get('quantity'),
                entry_price=deal_data.get('entry_price'),
                target_price=deal_data.get('target_price'),
                stop_loss=deal_data.get('stop_loss'),
                position_type=deal_data.get('position_type', 'LONG'),
                deal_type=deal_data.get('deal_type', 'EQUITY'),
                status='ACTIVE',
                notes=deal_data.get('notes', ''),
                tags=deal_data.get('tags', ''),
                created_at=datetime.utcnow()
            )
            
            db.session.add(deal)
            db.session.commit()
            
            return deal.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error creating user deal: {e}")
            db.session.rollback()
            return None
    
    def update_user_deal(self, deal_id: int, user_id: int, update_data: Dict) -> Optional[Dict]:
        """Update an existing user deal"""
        try:
            deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()
            if not deal:
                return None
            
            for key, value in update_data.items():
                if hasattr(deal, key):
                    setattr(deal, key, value)
            
            deal.updated_at = datetime.utcnow()
            db.session.commit()
            
            return deal.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error updating user deal: {e}")
            db.session.rollback()
            return None
    
    def delete_user_deal(self, deal_id: int, user_id: int) -> bool:
        """Delete a user deal"""
        try:
            deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()
            if not deal:
                return False
            
            db.session.delete(deal)
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting user deal: {e}")
            db.session.rollback()
            return False

# Create a global instance for backward compatibility
dynamic_deals_service = DynamicUserDealsService()