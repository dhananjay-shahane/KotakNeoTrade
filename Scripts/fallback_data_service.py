"""
Fallback Data Service - Provides error handling and fallback data when external database is unavailable
This is used when the external PostgreSQL database connection fails, ensuring the UI remains functional
"""

import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def get_fallback_etf_signals_data():
    """
    Provide sample ETF signals data structure when external database is unavailable
    Uses real ETF symbols but with placeholder trading data for UI functionality
    """
    logger.info("🔄 Using fallback data service - external database unavailable")
    
    # Sample ETF trading signals with realistic structure
    sample_signals = [
        {
            'trade_signal_id': 1,
            'id': 1,
            'etf': 'NIFTYBEES',
            'symbol': 'NIFTYBEES',
            'thirty': 180.50,
            'dh': 2.35,
            'date': '2025-01-10',
            'pos': 1,
            'qty': 100,
            'ep': 175.25,
            'cmp': 180.50,
            'chan': 3.00,
            'inv': 17525.00,
            'tp': 185.00,
            'tva': 18050.00,
            'tpr': 2.99,
            'pl': 525.00,
            'ed': '',
            'exp': '',
            'pr': 0.0,
            'pp': 0.0,
            'iv': 17525.00,
            'ip': 3.00,
            'nt': '',
            'qt': '',
            'seven': 178.20,
            'ch': 1.29,
            'created_at': '2025-01-10T10:30:00'
        },
        {
            'trade_signal_id': 2,
            'id': 2,
            'etf': 'BANKBEES',
            'symbol': 'BANKBEES',
            'thirty': 520.75,
            'dh': 1.85,
            'date': '2025-01-09',
            'pos': 1,
            'qty': 50,
            'ep': 512.30,
            'cmp': 520.75,
            'chan': 1.65,
            'inv': 25615.00,
            'tp': 530.00,
            'tva': 26037.50,
            'tpr': 1.65,
            'pl': 422.50,
            'ed': '',
            'exp': '',
            'pr': 0.0,
            'pp': 0.0,
            'iv': 25615.00,
            'ip': 1.65,
            'nt': '',
            'qt': '',
            'seven': 518.90,
            'ch': 0.36,
            'created_at': '2025-01-09T14:15:00'
        },
        {
            'trade_signal_id': 3,
            'id': 3,
            'etf': 'JUNIORBEES',
            'symbol': 'JUNIORBEES',
            'thirty': 890.25,
            'dh': -0.85,
            'date': '2025-01-08',
            'pos': 1,
            'qty': 25,
            'ep': 897.50,
            'cmp': 890.25,
            'chan': -0.81,
            'inv': 22437.50,
            'tp': 920.00,
            'tva': 22256.25,
            'tpr': -0.81,
            'pl': -181.25,
            'ed': '',
            'exp': '',
            'pr': 0.0,
            'pp': 0.0,
            'iv': 22437.50,
            'ip': -0.81,
            'nt': '',
            'qt': '',
            'seven': 895.10,
            'ch': -0.54,
            'created_at': '2025-01-08T11:45:00'
        }
    ]
    
    return {
        'data': sample_signals,
        'recordsTotal': len(sample_signals),
        'recordsFiltered': len(sample_signals),
        'message': 'Sample ETF signals data displayed. Connect database for real trading data.',
        'status': 'success',
        'fallback': True,
        'timestamp': datetime.now().isoformat()
    }

def get_fallback_error_response(error_message="Database connection failed"):
    """
    Generate a consistent error response for database connection failures
    """
    return {
        'success': False,
        'data': [],
        'recordsTotal': 0,
        'recordsFiltered': 0,
        'error': error_message,
        'message': f'Database connection error: {error_message}',
        'status': 'error',
        'fallback': True,
        'timestamp': datetime.now().isoformat()
    }

def test_external_database_availability():
    """
    Test if external database is available without timeout
    """
    try:
        from Scripts.external_db_service import test_database_connection
        return test_database_connection()
    except Exception as e:
        logger.error(f"External database test failed: {e}")
        return False