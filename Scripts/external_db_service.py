"""
External Database Service for fetching data from admin_trade_signals table
Connects to external PostgreSQL database and provides ETF signals data
"""

import psycopg2
import psycopg2.extras
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class ExternalDBService:
    """Service for connecting to external PostgreSQL database"""
    
    def __init__(self):
        self.db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
        self.connection = None
        
    def connect(self):
        """Establish connection to external database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✓ Connected to external PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to external database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✓ Disconnected from external database")
    
    def get_admin_trade_signals(self) -> List[Dict]:
        """Fetch all admin trade signals from external database"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                SELECT 
                    id,
                    etf,
                    symbol,
                    thirty,
                    dh,
                    date,
                    pos,
                    qty,
                    ep,
                    cmp,
                    chan,
                    inv,
                    tp,
                    tva,
                    tpr,
                    pl,
                    ed,
                    exp,
                    pr,
                    pp,
                    iv,
                    ip,
                    nt,
                    qt,
                    seven,
                    ch,
                    created_at
                FROM admin_trade_signals 
                ORDER BY created_at DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert RealDictRow to regular dict and handle data types
                signals = []
                for row in results:
                    signal = dict(row)
                    
                    # Convert dates to string if they exist
                    if signal.get('date'):
                        signal['date'] = str(signal['date']) if signal['date'] else ''
                    if signal.get('created_at'):
                        signal['created_at'] = signal['created_at'].strftime('%Y-%m-%d %H:%M:%S') if signal['created_at'] else None
                    
                    # Ensure numeric fields are properly formatted
                    numeric_fields = ['pos', 'qty', 'ep', 'cmp', 'inv', 'tp', 'tva', 'pl', 'nt', 'qt']
                    
                    for field in numeric_fields:
                        if signal.get(field) is not None:
                            try:
                                signal[field] = float(signal[field])
                            except (ValueError, TypeError):
                                signal[field] = 0.0
                    
                    # Ensure string fields are properly formatted
                    string_fields = ['etf', 'symbol', 'thirty', 'dh', 'chan', 'tpr', 'ed', 'exp', 'pr', 'pp', 'iv', 'ip', 'seven', 'ch']
                    for field in string_fields:
                        if signal.get(field) is not None:
                            signal[field] = str(signal[field])
                        else:
                            signal[field] = ''
                    
                    signals.append(signal)
                
                logger.info(f"✓ Fetched {len(signals)} admin trade signals from external database")
                return signals
            
        except Exception as e:
            logger.error(f"Error fetching admin trade signals: {e}")
            return []
    
    def get_signal_by_id(self, signal_id: int) -> Optional[Dict]:
        """Fetch specific admin trade signal by ID"""
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = """
            SELECT * FROM admin_trade_signals 
            WHERE id = %s
            """
            
            cursor.execute(query, (signal_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                signal = dict(result)
                # Format dates and numeric fields same as above
                if signal.get('entry_date'):
                    signal['entry_date'] = signal['entry_date'].strftime('%Y-%m-%d') if signal['entry_date'] else None
                if signal.get('exit_date'):
                    signal['exit_date'] = signal['exit_date'].strftime('%Y-%m-%d') if signal['exit_date'] else None
                
                return signal
            return None
            
        except Exception as e:
            logger.error(f"Error fetching signal by ID {signal_id}: {e}")
            return None

def get_etf_signals_from_external_db() -> List[Dict]:
    """Fetch ETF signals data from external admin_trade_signals table"""
    db_service = ExternalDBService()
    try:
        signals = db_service.get_admin_trade_signals()
        return signals
    finally:
        db_service.disconnect()

def get_yahoo_symbol_suffix(symbol):
    """Determine the appropriate Yahoo Finance suffix based on symbol"""
    symbol = symbol.upper().strip()
    
    # ETF symbols - typically use .NS for NSE-listed ETFs
    etf_symbols = [
        'NIFTYBEES', 'JUNIORBEES', 'GOLDBEES', 'SILVERBEES', 'BANKBEES',
        'CONSUMBEES', 'PHARMABEES', 'AUTOIETF', 'FMCGIETF', 'FINIETF',
        'INFRABEES', 'TNIDETF', 'MOM30IETF', 'HDFCPVTBAN', 'ITBEES',
        'MID150BEES', 'LIQUIDBEES', 'PSUBNKBEES', 'PVTBNKBEES'
    ]
    
    # Large cap stocks - use .NS for NSE
    large_cap_stocks = [
        'RELIANCE', 'TCS', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'HDFCBANK',
        'ITC', 'SBIN', 'BHARTIARTL', 'LT', 'WIPRO', 'MARUTI', 'ASIANPAINT',
        'KOTAKBANK', 'HCLTECH', 'AXISBANK', 'ULTRACEMCO', 'BAJFINANCE',
        'SUNPHARMA', 'TITAN', 'NESTLEIND', 'POWERGRID', 'NTPC', 'ONGC',
        'TATAMOTORS', 'TATASTEEL', 'COALINDIA', 'BAJAJFINSV', 'M&M'
    ]
    
    # BSE-specific symbols (use .BO)
    bse_symbols = [
        'SENSEX', 'BSE500', 'BSESMCAP', 'BSEMIDCAP'
    ]
    
    # Special cases for different exchanges
    if symbol in bse_symbols:
        return f"{symbol}.BO"
    elif symbol in etf_symbols or symbol in large_cap_stocks:
        return f"{symbol}.NS"
    else:
        # Default to NSE for Indian symbols
        return f"{symbol}.NS"

def get_etf_signals_data_json():
    """Get ETF signals data in JSON format for API response"""
    try:
        signals = get_etf_signals_from_external_db()
        
        # Format data for frontend datatable matching the exact schema
        formatted_signals = []
        for signal in signals:
            formatted_signal = {
                'id': signal.get('id', ''),
                'etf': signal.get('etf', '') or signal.get('symbol', ''),
                'thirty': signal.get('thirty', '30'),
                'dh': signal.get('dh', 'DH'),
                'date': signal.get('date', ''),
                'pos': signal.get('pos', 0),
                'qty': signal.get('qty', 0),
                'ep': signal.get('ep', 0),
                'cmp': signal.get('cmp', 0),
                'chan': signal.get('chan', ''),
                'inv': signal.get('inv', 0),
                'tp': signal.get('tp', 0),
                'tva': signal.get('tva', 0),
                'tpr': signal.get('tpr', ''),
                'pl': signal.get('pl', 0),
                'ed': signal.get('ed', ''),
                'exp': signal.get('exp', ''),
                'pr': signal.get('pr', ''),
                'pp': signal.get('pp', ''),
                'iv': signal.get('iv', ''),
                'ip': signal.get('ip', ''),
                'nt': signal.get('nt', 0),
                'qt': signal.get('qt', 0),
                'seven': signal.get('seven', ''),
                'ch': signal.get('ch', ''),
                'symbol': signal.get('symbol', '') or signal.get('etf', ''),
                'trade_signal_id': signal.get('id', ''),
            }
            formatted_signals.append(formatted_signal)
        
        return {
            'data': formatted_signals,
            'recordsTotal': len(formatted_signals),
            'recordsFiltered': len(formatted_signals)
        }
        
    except Exception as e:
        logger.error(f"Error getting ETF signals data: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'error': str(e)
        }