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
    Provide fallback data structure when external database is unavailable
    Returns empty data structure to maintain UI functionality
    """
    logger.info("🔄 Using fallback data service - external database unavailable")
    
    return {
        'data': [],
        'recordsTotal': 0,
        'recordsFiltered': 0,
        'message': 'External database connection failed. Please configure database credentials.',
        'status': 'error',
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