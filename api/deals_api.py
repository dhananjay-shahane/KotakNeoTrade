"""
Deals API - External Database Integration
Handles all deals-related operations with external PostgreSQL database
"""
import logging
from flask import Blueprint, request, jsonify, session
import psycopg2
import psycopg2.extras
from datetime import datetime
import traceback
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

deals_api = Blueprint('deals_api', __name__, url_prefix='/api')

@deals_api.route('/test-deals', methods=['GET'])
def test_deals():
    """Test endpoint to verify blueprint registration"""
    return jsonify({
        'message': 'Deals API blueprint is working',
        'success': True
    })

def get_external_db_connection():
    """Get connection to external PostgreSQL database"""
    try:
        database_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db"
        conn = psycopg2.connect(database_url)
        logger.info("✓ Connected to external PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to external database: {e}")
        return None

def get_user_deals_from_db():
    """
    Get user deals from external database public.user_deals table
    Returns all authentic deals with proper structure for calculations
    """
    try:
        conn = get_external_db_connection()
        if not conn:
            logger.error("Failed to connect to external database")
            return []

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Query to get all user deals from external database
            query = """
            SELECT 
                id,
                user_id,
                symbol,
                trading_symbol,
                entry_date,
                position_type,
                quantity,
                entry_price,
                current_price,
                target_price,
                stop_loss,
                invested_amount,
                current_value,
                pnl_amount,
                pnl_percent,
                status,
                deal_type,
                notes,
                tags,
                created_at,
                updated_at
            FROM public.user_deals 
            WHERE status = 'ACTIVE'
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            deals = []
            for row in rows:
                deal = dict(row)
                # Ensure numeric fields are properly formatted
                deal['entry_price'] = float(deal['entry_price']) if deal['entry_price'] else 0.0
                deal['current_price'] = float(deal['current_price']) if deal['current_price'] else 0.0
                deal['invested_amount'] = float(deal['invested_amount']) if deal['invested_amount'] else 0.0
                deal['current_value'] = float(deal['current_value']) if deal['current_value'] else 0.0
                deal['pnl_amount'] = float(deal['pnl_amount']) if deal['pnl_amount'] else 0.0
                deal['pnl_percent'] = float(deal['pnl_percent']) if deal['pnl_percent'] else 0.0
                deals.append(deal)
            
        conn.close()
        logger.info(f"✓ Fetched {len(deals)} user deals from external database")
        return deals

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        traceback.print_exc()
        return []

@deals_api.route('/user-deals-data')
def get_user_deals_data():
    """API endpoint to get user deals data from external database"""
    try:
        deals = get_user_deals_from_db()
        
        # Calculate summary
        total_invested = sum(deal.get('invested_amount', 0) for deal in deals)
        total_current = sum(deal.get('current_value', 0) for deal in deals)
        total_pnl = total_current - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            'success': True,
            'deals': deals,
            'summary': {
                'total_deals': len(deals),
                'total_invested': total_invested,
                'total_current_value': total_current,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent
            }
        })
        
    except Exception as e:
        logger.error(f"Error in user deals API: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'deals': [],
            'summary': {
                'total_deals': 0,
                'total_invested': 0,
                'total_current_value': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0
            }
        }), 500

@deals_api.route('/deals/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a new deal from trading signal using local JSON storage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Extract signal data
        signal_data = data.get('signal_data', {})
        
        # Helper functions for safe conversion
        def safe_float(value, default=0.0):
            if value is None or value == '' or value == '--':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=1):
            if value is None or value == '':
                return default
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default

        # Get required fields with safe conversion
        symbol = signal_data.get('symbol') or signal_data.get('etf', '')
        if not symbol or symbol == 'UNKNOWN':
            return jsonify({
                'success': False,
                'error': 'Missing or invalid symbol'
            }), 400

        qty = safe_int(signal_data.get('qty'), 1)
        ep = safe_float(signal_data.get('ep'), 0.0)
        cmp = signal_data.get('cmp')
        
        # Handle CMP - if it's "--" or invalid, use entry price
        if cmp == "--" or cmp is None or cmp == '':
            cmp = ep
        else:
            cmp = safe_float(cmp, ep)
        
        pos = safe_int(signal_data.get('pos'), 1)
        
        # Set user_id - handle both string and integer user_ids safely
        session_user_id = session.get('user_id', 1)
        
        # Convert user_id to integer safely, fallback to 1 if invalid
        try:
            if isinstance(session_user_id, str):
                if session_user_id.isdigit():
                    user_id = int(session_user_id)
                else:
                    logger.info(f"Non-numeric user_id in session: {session_user_id}, using default user_id = 1")
                    user_id = 1
            elif isinstance(session_user_id, int):
                user_id = session_user_id
            else:
                user_id = 1
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id in session: {session_user_id}, using default user_id = 1")
            user_id = 1

        # Validate required data
        if ep <= 0 or qty <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid price or quantity data'
            }), 400

        if not symbol or len(symbol.strip()) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol'
            }), 400

        if user_id <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid user ID'
            }), 400

        # Calculate target price safely
        tp = safe_float(signal_data.get('tp'), ep * 1.05)
        if tp <= 0:
            tp = ep * 1.05

        # Calculate values
        invested_amount = ep * qty
        current_value = cmp * qty
        pnl_amount = current_value - invested_amount
        pnl_percent = (pnl_amount / invested_amount * 100) if invested_amount > 0 else 0

        # Connect to external database
        conn = get_external_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'External database connection failed'
            }), 500

        # Ensure user_id is positive
        if not user_id or user_id <= 0:
            user_id = 1

        try:
            with conn.cursor() as cursor:
                # Insert new deal into public.user_deals table
                insert_query = """
                INSERT INTO public.user_deals (
                    user_id, symbol, trading_symbol, entry_date, position_type,
                    quantity, entry_price, current_price, target_price, stop_loss,
                    invested_amount, current_value, pnl_amount, pnl_percent,
                    status, deal_type, notes, tags, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
                """
                
                values = (
                    user_id,
                    symbol.upper(),
                    symbol.upper(),
                    datetime.now().strftime('%Y-%m-%d'),
                    'LONG' if pos == 1 else 'SHORT',
                    qty,
                    float(ep),
                    float(cmp),
                    float(tp),
                    float(ep * 0.95),  # Default 5% stop loss
                    float(invested_amount),
                    float(current_value),
                    float(pnl_amount),
                    float(pnl_percent),
                    'ACTIVE',
                    'SIGNAL',
                    f'Added from ETF signal - {symbol}',
                    'ETF,SIGNAL',
                    datetime.now(),
                    datetime.now()
                )

                logger.info(f"Executing insert query with values: {values}")
                cursor.execute(insert_query, values)
                deal_id = cursor.fetchone()[0]
                conn.commit()

                logger.info(f"✓ Created deal from signal: {symbol} - Deal ID: {deal_id} for user: {user_id}")

                return jsonify({
                    'success': True,
                    'message': f'Deal created successfully for {symbol}',
                    'deal_id': deal_id,
                    'symbol': symbol,
                    'entry_price': ep,
                    'quantity': qty,
                    'invested_amount': invested_amount
                })

        finally:
            if conn:
                conn.close()

    except Exception as db_error:
        logger.error(f"Database error creating deal: {db_error}")
        logger.error(f"Signal data was: {signal_data}")
        logger.error(f"Processed values were: user_id={user_id}, symbol={symbol}, qty={qty}, ep={ep}, cmp={cmp}")
        return jsonify({
            'success': False,
            'error': f'Failed to create deal: {str(db_error)}'
        }), 500