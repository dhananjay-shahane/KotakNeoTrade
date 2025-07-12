"""
Deals API - Separate API for User Deals functionality
Handles all deals-related operations with proper calculations and database integration
"""
import logging
from flask import Blueprint, request, jsonify, session
from core.database import get_db_connection
from core.auth import require_auth
from datetime import datetime, timedelta
import traceback
import psycopg2.extras
from Scripts.user_deals_service import get_user_deals_data

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

def get_user_deals_from_db():
    """
    Get user deals from user_deals table (real data only)
    Returns all authentic deals with proper structure for calculations
    """
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return []

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Query to get all user deals - only real data
            query = """
            SELECT 
                id,
                symbol,
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
                updated_at,
                pos,
                qty,
                ep,
                cmp,
                tp,
                inv,
                pl
            FROM user_deals 
            WHERE symbol IS NOT NULL AND symbol != ''
            ORDER BY created_at DESC
            """

            cursor.execute(query)
            deals = []

            for row in cursor.fetchall():
                deal = dict(row)
                # Only include deals with valid trading data
                if deal.get('symbol') and deal.get('quantity') and deal.get('entry_price'):
                    deals.append(deal)

            logger.info(f"✓ Fetched {len(deals)} authentic user deals from database")

            # If no deals found, return empty with clear message
            if len(deals) == 0:
                logger.info("No user deals found in database - user needs to add real trading data")

            return deals

    except Exception as e:
        logger.error(f"❌ Error fetching user deals: {e}")
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def calculate_deal_metrics(deal):
    """
    Calculate all metrics for a single deal based on the provided requirements
    """
    try:
        # Get basic trading data with proper null handling
        symbol = str(deal.get('symbol', '')).strip().upper()
        if not symbol or symbol == 'N/A':
            symbol = 'UNKNOWN'

        # Position type: LONG or SHORT
        position_type = str(deal.get('position_type', 'LONG')).upper()

        # Status: ACTIVE, CLOSED, etc.
        status = str(deal.get('status', 'ACTIVE')).upper()

        # Handle numeric fields with null safety using correct column names
        quantity = float(deal.get('quantity', 0)) if deal.get('quantity') is not None else 0.0
        entry_price = float(deal.get('entry_price', 0)) if deal.get('entry_price') is not None else 0.0
        current_price = float(deal.get('current_price', 0)) if deal.get('current_price') is not None else 0.0

        # Use the existing calculated values from the database
        target_price = float(deal.get('target_price', 0)) if deal.get('target_price') is not None else 0.0
        stop_loss = float(deal.get('stop_loss', 0)) if deal.get('stop_loss') is not None else 0.0
        invested_amount = float(deal.get('invested_amount', 0)) if deal.get('invested_amount') is not None else 0.0
        current_value = float(deal.get('current_value', 0)) if deal.get('current_value') is not None else 0.0
        pnl_amount = float(deal.get('pnl_amount', 0)) if deal.get('pnl_amount') is not None else 0.0
        pnl_percent = float(deal.get('pnl_percent', 0)) if deal.get('pnl_percent') is not None else 0.0

        # Calculate additional metrics if needed
        if invested_amount == 0 and quantity > 0 and entry_price > 0:
            invested_amount = quantity * entry_price

        if current_value == 0 and quantity > 0 and current_price > 0:
            current_value = quantity * current_price

        if pnl_amount == 0 and invested_amount > 0 and current_value > 0:
            pnl_amount = current_value - invested_amount

        if pnl_percent == 0 and invested_amount > 0 and pnl_amount != 0:
            pnl_percent = (pnl_amount / invested_amount) * 100

        # Status color based on PnL
        if pnl_amount > 0:
            status_color = 'success'
            status_text = 'Profit'
        elif pnl_amount < 0:
            status_color = 'danger'
            status_text = 'Loss'
        else:
            status_color = 'secondary'
            status_text = 'Break Even'

        return {
            'id': deal.get('id', ''),
            'symbol': symbol,
            'entry_date': deal.get('entry_date', ''),
            'position_type': position_type,
            'status': status,
            'quantity': int(quantity),
            'entry_price': round(entry_price, 2),
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'invested_amount': round(invested_amount, 2),
            'current_value': round(current_value, 2),
            'pnl_amount': round(pnl_amount, 2),
            'pnl_percent': round(pnl_percent, 2),
            'status_color': status_color,
            'status_text': status_text,
            'deal_type': deal.get('deal_type', ''),
            'notes': deal.get('notes', ''),
            'tags': deal.get('tags', ''),
            # Formatted display values
            'entry_price_formatted': f"₹{entry_price:.2f}",
            'current_price_formatted': f"₹{current_price:.2f}",
            'invested_amount_formatted': f"₹{invested_amount:.2f}",
            'pnl_amount_formatted': f"₹{pnl_amount:.2f}",
            'target_price_formatted': f"₹{target_price:.2f}",
            'stop_loss_formatted': f"₹{stop_loss:.2f}",
            'current_value_formatted': f"₹{current_value:.2f}",
            'pnl_percent_formatted': f"{pnl_percent:.2f}%",
            'created_at': deal.get('created_at', ''),
            'updated_at': deal.get('updated_at', '')
        }

    except Exception as e:
        logger.error(f"Error calculating metrics for deal {deal.get('id', 'unknown')}: {e}")
        return None

@deals_api.route('/user-deals', methods=['GET'])
def get_user_deals():
    """
    API endpoint to get user deals with all calculations
    Returns properly formatted data for DataTable
    """
    try:
        # Get deals from database with CMP from symbols schema
        deals = get_user_deals_data()

        if not deals:
            logger.info("No user deals found - database is empty")
            return jsonify({
                'success': True,
                'data': [],
                'deals': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'total': 0,
                'message': 'No trading deals found. Please add your real trading data to the user_deals table.',
                'instructions': 'Use real trading data from your broker account - no sample data allowed.'
            })

        # Format deals for frontend display
        formatted_deals = []
        for deal in deals:
            formatted_deal = {
                'id': deal.get('id'),
                'symbol': deal.get('symbol', '').upper(),
                'entry_date': deal.get('entry_date'),
                'pos': deal.get('position_type', 'LONG'),
                'qty': float(deal.get('quantity', 0)),
                'ep': float(deal.get('entry_price', 0)),
                'cmp': float(deal.get('cmp', 0)),
                'tp': float(deal.get('target_price', 0)),
                'sl': float(deal.get('stop_loss', 0)),
                'inv': float(deal.get('invested_amount', 0)),
                'cv': float(deal.get('current_value', 0)),
                'pl': float(deal.get('pnl_amount', 0)),
                'pl_percent': float(deal.get('pnl_percent', 0)),
                'status': deal.get('status', 'ACTIVE'),
                'deal_type': deal.get('deal_type', 'EQUITY'),
                'notes': deal.get('notes', ''),
                'tags': deal.get('tags', ''),
                'created_at': deal.get('created_at'),
                'updated_at': deal.get('updated_at'),
                # Formatted values for display
                'ep_formatted': f"₹{float(deal.get('entry_price', 0)):.2f}",
                'cmp_formatted': f"₹{float(deal.get('cmp', 0)):.2f}",
                'tp_formatted': f"₹{float(deal.get('target_price', 0)):.2f}",
                'sl_formatted': f"₹{float(deal.get('stop_loss', 0)):.2f}",
                'inv_formatted': f"₹{float(deal.get('invested_amount', 0)):.2f}",
                'cv_formatted': f"₹{float(deal.get('current_value', 0)):.2f}",
                'pl_formatted': f"₹{float(deal.get('pnl_amount', 0)):.2f}",
                'pl_percent_formatted': f"{float(deal.get('pnl_percent', 0)):.2f}%"
            }
            formatted_deals.append(formatted_deal)

        # Sort by creation date (newest first)
        formatted_deals.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        total_deals = len(formatted_deals)
        success_message = f"✅ Successfully processed {total_deals} deals with CMP from symbols schema."

        logger.info(success_message)

        return jsonify({
            'success': True,
            'data': formatted_deals,
            'deals': formatted_deals,
            'recordsTotal': total_deals,
            'recordsFiltered': total_deals,
            'total': total_deals,
            'message': success_message
        })

    except Exception as e:
        logger.error(f"❌ Error in get_user_deals API: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'data': [],
            'deals': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'total': 0,
            'error': str(e),
            'message': f'❌ Error loading deals: {str(e)}'
        }), 500

@deals_api.route('/deals-summary', methods=['GET'])
def get_deals_summary():
    """
    Get summary statistics for user deals
    """
    try:
        raw_deals = get_user_deals_from_db()

        if not raw_deals:
            return jsonify({
                'total_deals': 0,
                'running_deals': 0,
                'closed_deals': 0,
                'total_investment': 0,
                'total_pl': 0,
                'success_rate': 0
            })

        total_deals = len(raw_deals)
        running_deals = sum(1 for deal in raw_deals if deal.get('status', 1) == 1)
        closed_deals = total_deals - running_deals

        total_investment = 0
        total_pl = 0
        profitable_deals = 0

        for deal in raw_deals:
            calculated = calculate_deal_metrics(deal)
            if calculated:
                total_investment += calculated['inv']
                total_pl += calculated['pl']
                if calculated['pl'] > 0:
                    profitable_deals += 1

        success_rate = (profitable_deals / total_deals * 100) if total_deals > 0 else 0

        return jsonify({
            'total_deals': total_deals,
            'running_deals': running_deals,
            'closed_deals': closed_deals,
            'total_investment': round(total_investment, 2),
            'total_pl': round(total_pl, 2),
            'success_rate': round(success_rate, 2),
            'profitable_deals': profitable_deals
        })

    except Exception as e:
        logger.error(f"❌ Error in get_deals_summary: {e}")
        return jsonify({'error': str(e)}), 500

@deals_api.route('/deals/<int:deal_id>', methods=['GET'])
def get_deal_details(deal_id):
    """
    Get detailed information for a specific deal
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        with conn.cursor() as cursor:
            query = """
            SELECT * FROM user_deals WHERE id = %s
            """
            cursor.execute(query, (deal_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()

            if not row:
                return jsonify({'error': 'Deal not found'}), 404

            deal = dict(zip(columns, row))
            calculated_deal = calculate_deal_metrics(deal)

            if calculated_deal:
                calculated_deal['id'] = deal['id']
                return jsonify(calculated_deal)
            else:
                return jsonify({'error': 'Error calculating deal metrics'}), 500

    except Exception as e:
        logger.error(f"❌ Error in get_deal_details: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@deals_api.route('/deals/add', methods=['POST'])
def add_deal():
    """
    Add a new trading deal to user_deals table
    Only accepts real trading data - no sample data
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['symbol', 'qty', 'ep', 'pos']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate numeric fields
        try:
            qty = float(data['qty'])
            ep = float(data['ep'])
            pos = int(data['pos'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid numeric values provided'}), 400

        # Validate position type
        if pos not in [1, -1]:
            return jsonify({'error': 'Position must be 1 (buy) or -1 (sell)'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        with conn.cursor() as cursor:
            # Insert new deal
            query = """
            INSERT INTO user_deals (symbol, date, pos, qty, ep, cmp, d30, d7, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            values = (
                data['symbol'].upper(),
                data.get('date', 'CURRENT_DATE'),
                pos,
                qty,
                ep,
                data.get('cmp', 0),
                data.get('d30', 0),
                data.get('d7', 0),
                data.get('status', 1)
            )

            cursor.execute(query, values)
            deal_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(f"✓ Added new deal: {data['symbol']} - ID: {deal_id}")

            return jsonify({
                'success': True,
                'message': f'Deal added successfully: {data["symbol"]}',
                'deal_id': deal_id
            })

    except Exception as e:
        logger.error(f"❌ Error adding deal: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@deals_api.route('/deals/bulk-import', methods=['POST'])
def bulk_import_deals():
    """
    Bulk import trading deals from authentic broker data
    Accepts CSV or JSON format with real trading data
    """
    try:
        data = request.get_json()

        if not data or 'deals' not in data:
            return jsonify({'error': 'No deals data provided'}), 400

        deals_data = data['deals']
        if not isinstance(deals_data, list):
            return jsonify({'error': 'Deals data must be an array'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        imported_count = 0
        errors = []

        with conn.cursor() as cursor:
            for i, deal in enumerate(deals_data):
                try:
                    # Validate each deal
                    if not deal.get('symbol') or not deal.get('qty') or not deal.get('ep'):
                        errors.append(f"Row {i+1}: Missing required fields")
                        continue

                    # Insert deal
                    query = """
                    INSERT INTO user_deals (symbol, date, pos, qty, ep, cmp, d30, d7, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        deal['symbol'].upper(),
                        deal.get('date', 'CURRENT_DATE'),
                        int(deal.get('pos', 1)),
                        float(deal['qty']),
                        float(deal['ep']),
                        float(deal.get('cmp', 0)),
                        float(deal.get('d30', 0)),
                        float(deal.get('d7', 0)),
                        int(deal.get('status', 1))
                    )

                    cursor.execute(query, values)
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")

            conn.commit()

        logger.info(f"✓ Bulk imported {imported_count} deals")

        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} deals',
            'imported_count': imported_count,
            'errors': errors
        })

    except Exception as e:
        logger.error(f"❌ Error in bulk import: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@deals_api.route('/api/deals/user', methods=['GET'])
def get_user_deals_api():
    """Get deals for current user with optional symbol filter"""
    try:
        symbol = request.args.get('symbol', '')

        # For now, return empty deals to prevent 404 errors
        # This can be expanded later with actual user authentication and deal fetching
        return jsonify({
            'success': True,
            'deals': [],
            'total': 0,
            'message': f'No existing deals found for symbol: {symbol}' if symbol else 'No deals found'
        })

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'deals': [],
            'total': 0
        }), 500

@deals_api.route('/deals/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a deal from ETF signal and save to user_deals table"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Extract signal data
        signal_data = data.get('signal_data', {})
        
        # Get required fields with fallbacks
        symbol = signal_data.get('symbol') or signal_data.get('etf', 'UNKNOWN')
        qty = float(signal_data.get('qty', 1))
        ep = float(signal_data.get('ep', 0))
        cmp = signal_data.get('cmp')
        
        # Handle CMP - if it's "--" or invalid, use entry price
        if cmp == "--" or cmp is None:
            cmp = ep
        else:
            cmp = float(cmp)
        
        pos = int(signal_data.get('pos', 1))
        tp = float(signal_data.get('tp', ep * 1.05))  # Default 5% target
        
        # Validate required data
        if not symbol or symbol == 'UNKNOWN' or ep <= 0 or qty <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid signal data - missing symbol, price, or quantity'
            }), 400

        # Calculate values
        invested_amount = ep * qty
        current_value = cmp * qty
        pnl_amount = current_value - invested_amount
        pnl_percent = (pnl_amount / invested_amount * 100) if invested_amount > 0 else 0

        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500

        # Get user_id from session or create/use default user
        user_id = session.get('user_id')
        
        if not user_id:
            # Create or get default user
            try:
                with conn.cursor() as cursor:
                    # Check if default user exists
                    cursor.execute("SELECT id FROM users WHERE ucc = %s", ('DEFAULT_USER',))
                    result = cursor.fetchone()
                    
                    if result:
                        user_id = result[0]
                    else:
                        # Create default user
                        cursor.execute("""
                            INSERT INTO users (ucc, mobile_number, greeting_name, is_active)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, ('DEFAULT_USER', '9999999999', 'Default User', True))
                        user_id = cursor.fetchone()[0]
                        conn.commit()
                        logger.info(f"Created default user with ID: {user_id}")
            except Exception as user_error:
                logger.warning(f"Could not create default user: {user_error}")
                user_id = 1  # Fallback to ID 1

        try:
            with conn.cursor() as cursor:
                # Prepare proper date value
                entry_date = signal_data.get('date')
                if not entry_date or entry_date == 'CURRENT_DATE':
                    entry_date = datetime.now().strftime('%Y-%m-%d')

                # Insert into user_deals table with proper values
                insert_query = """
                    INSERT INTO user_deals (
                        user_id, symbol, trading_symbol, entry_date, position_type, quantity, entry_price,
                        current_price, target_price, stop_loss, invested_amount,
                        current_value, pnl_amount, pnl_percent, status, deal_type,
                        notes, tags, created_at, updated_at,
                        pos, qty, ep, cmp, tp, inv, pl
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(),
                        %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """
                
                values = (
                    user_id,  # user_id
                    symbol.upper(),  # symbol
                    f"{symbol.upper()}-EQ",  # trading_symbol - proper format
                    entry_date,  # entry_date
                    'LONG' if pos == 1 else 'SHORT',  # position_type
                    int(qty),  # quantity
                    float(ep),  # entry_price
                    float(cmp),  # current_price
                    float(tp),  # target_price
                    float(ep * 0.95),  # stop_loss - 5% below entry
                    float(invested_amount),  # invested_amount
                    float(current_value),  # current_value
                    float(pnl_amount),  # pnl_amount
                    float(pnl_percent),  # pnl_percent
                    'ACTIVE',  # status
                    'SIGNAL',  # deal_type
                    f'Added from ETF signal - {symbol}',  # notes
                    'ETF,SIGNAL',  # tags
                    # created_at and updated_at are handled by NOW() in query
                    int(pos),  # pos
                    int(qty),  # qty
                    float(ep),  # ep
                    float(cmp),  # cmp
                    float(tp),  # tp
                    float(invested_amount),  # inv
                    float(pnl_amount)  # pl
                )

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

        except Exception as db_error:
            logger.error(f"Database error creating deal: {db_error}")
            if conn:
                conn.rollback()
            return jsonify({
                'success': False,
                'error': f'Failed to create deal: {str(db_error)}'
            }), 500
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"Error creating deal from signal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500