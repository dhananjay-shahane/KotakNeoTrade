#!/usr/bin/env python3
"""
Populate admin_trade_signals table with sample ETF signals data
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from scripts.models_etf import AdminTradeSignal
from scripts.models import User

def create_admin_user():
    """Create admin user if not exists"""
    admin_user = User.query.filter_by(ucc='admin').first()
    if not admin_user:
        admin_user = User(
            ucc='admin',
            mobile_number='9999999999',
            greeting_name='Admin User',
            user_id='admin',
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Created admin user")
    return admin_user

def create_target_user():
    """Create target user if not exists"""
    target_user = User.query.filter_by(ucc='zhz3j').first()
    if not target_user:
        target_user = User(
            ucc='zhz3j',
            mobile_number='9876543210',
            greeting_name='ETF Trader',
            user_id='zhz3j',
            is_active=True
        )
        db.session.add(target_user)
        db.session.commit()
        print("✓ Created target user")
    return target_user

def populate_admin_signals():
    """Populate admin_trade_signals table with sample ETF data"""
    
    admin_user = create_admin_user()
    target_user = create_target_user()
    
    # Clear existing signals
    AdminTradeSignal.query.delete()
    db.session.commit()
    print("✓ Cleared existing signals")
    
    # Sample ETF signals data
    etf_signals = [
        {
            'symbol': 'NIFTYBEES',
            'signal_type': 'BUY',
            'entry_price': Decimal('245.50'),
            'target_price': Decimal('260.00'),
            'stop_loss': Decimal('235.00'),
            'quantity': 100,
            'signal_title': 'NIFTY ETF - Bullish Breakout',
            'signal_description': 'Strong momentum with volume surge. Target 260.',
            'priority': 'HIGH'
        },
        {
            'symbol': 'BANKBEES',
            'signal_type': 'BUY',
            'entry_price': Decimal('520.75'),
            'target_price': Decimal('545.00'),
            'stop_loss': Decimal('505.00'),
            'quantity': 50,
            'signal_title': 'Bank ETF - Sector Rotation',
            'signal_description': 'Banking sector showing strength. Good risk-reward.',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'GOLDSHARE',
            'signal_type': 'SELL',
            'entry_price': Decimal('4850.00'),
            'target_price': Decimal('4720.00'),
            'stop_loss': Decimal('4920.00'),
            'quantity': 10,
            'signal_title': 'Gold ETF - Correction Expected',
            'signal_description': 'Overbought levels, expect pullback to 4720.',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'ITBEES',
            'signal_type': 'BUY',
            'entry_price': Decimal('425.30'),
            'target_price': Decimal('445.00'),
            'stop_loss': Decimal('415.00'),
            'quantity': 75,
            'signal_title': 'IT ETF - Tech Recovery',
            'signal_description': 'IT sector bouncing from support. Good entry.',
            'priority': 'HIGH'
        },
        {
            'symbol': 'LIQUIDBEES',
            'signal_type': 'BUY',
            'entry_price': Decimal('1000.00'),
            'target_price': Decimal('1002.00'),
            'stop_loss': Decimal('999.50'),
            'quantity': 200,
            'signal_title': 'Liquid ETF - Safe Haven',
            'signal_description': 'Market volatility hedge, low risk trade.',
            'priority': 'LOW'
        },
        {
            'symbol': 'AXISGOLD',
            'signal_type': 'BUY',
            'entry_price': Decimal('4780.00'),
            'target_price': Decimal('4950.00'),
            'stop_loss': Decimal('4650.00'),
            'quantity': 8,
            'signal_title': 'Axis Gold ETF - Breakout',
            'signal_description': 'Gold breaking resistance, momentum trade.',
            'priority': 'HIGH'
        },
        {
            'symbol': 'CPSE',
            'signal_type': 'BUY',
            'entry_price': Decimal('38.50'),
            'target_price': Decimal('42.00'),
            'stop_loss': Decimal('36.00'),
            'quantity': 500,
            'signal_title': 'CPSE ETF - Value Play',
            'signal_description': 'PSU revival theme, good value at current levels.',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'JUNIORBEES',
            'signal_type': 'SELL',
            'entry_price': Decimal('168.75'),
            'target_price': Decimal('162.00'),
            'stop_loss': Decimal('172.00'),
            'quantity': 150,
            'signal_title': 'Junior Nifty - Weakness',
            'signal_description': 'Mid-cap showing weakness, expect correction.',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'KOTAKSILV',
            'signal_type': 'BUY',
            'entry_price': Decimal('6250.00'),
            'target_price': Decimal('6500.00'),
            'stop_loss': Decimal('6100.00'),
            'quantity': 5,
            'signal_title': 'Silver ETF - Precious Metals Rally',
            'signal_description': 'Silver outperforming gold, momentum trade.',
            'priority': 'HIGH'
        },
        {
            'symbol': 'HDFCNIFTY',
            'signal_type': 'BUY',
            'entry_price': Decimal('248.20'),
            'target_price': Decimal('262.00'),
            'stop_loss': Decimal('240.00'),
            'quantity': 80,
            'signal_title': 'HDFC Nifty ETF - Index Play',
            'signal_description': 'Nifty showing strength, index outperformance.',
            'priority': 'MEDIUM'
        }
    ]
    
    # Create signals
    for signal_data in etf_signals:
        signal = AdminTradeSignal(
            admin_user_id=admin_user.id,
            target_user_id=target_user.id,
            symbol=signal_data['symbol'],
            trading_symbol=f"{signal_data['symbol']}-EQ",
            signal_type=signal_data['signal_type'],
            entry_price=signal_data['entry_price'],
            target_price=signal_data['target_price'],
            stop_loss=signal_data['stop_loss'],
            quantity=signal_data['quantity'],
            signal_title=signal_data['signal_title'],
            signal_description=signal_data['signal_description'],
            priority=signal_data['priority'],
            status='ACTIVE',
            created_at=datetime.now() - timedelta(days=1),  # Created yesterday
            signal_date=datetime.now().date(),
            expiry_date=(datetime.now() + timedelta(days=30)).date(),
            # Calculate initial values
            investment_amount=signal_data['entry_price'] * signal_data['quantity'],
            current_price=signal_data['entry_price'],  # Will be updated by Kotak quotes
            current_value=signal_data['entry_price'] * signal_data['quantity'],
            pnl=Decimal('0.00'),
            pnl_percentage=Decimal('0.00')
        )
        db.session.add(signal)
    
    db.session.commit()
    print(f"✓ Created {len(etf_signals)} ETF signals in admin_trade_signals table")
    
    # Display summary
    total_signals = AdminTradeSignal.query.count()
    active_signals = AdminTradeSignal.query.filter_by(status='ACTIVE').count()
    print(f"✓ Total signals: {total_signals}")
    print(f"✓ Active signals: {active_signals}")
    print(f"✓ Admin user ID: {admin_user.id}")
    print(f"✓ Target user ID: {target_user.id}")

if __name__ == '__main__':
    with app.app_context():
        try:
            populate_admin_signals()
            print("\n✅ Successfully populated admin_trade_signals table!")
            print("📊 ETF signals page will now show real data from database")
            print("💹 Kotak Neo quotes will update CMP values when symbols match")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()