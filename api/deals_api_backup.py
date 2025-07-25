"""
Deals API - Separate API for User Deals functionality
Handles all deals-related operations with proper calculations and database integration
"""
import logging
from flask import Blueprint, request, jsonify, session
# Remove dependency on external PostgreSQL - use simple local storage instead
import json
import os
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
        # Use local JSON file storage instead of PostgreSQL
        deals_file = 'user_deals.json'
        
        if not os.path.exists(deals_file):
            logger.info("No deals file found, returning empty list")
            return []

        with open(deals_file, 'r') as f:
            all_deals = json.load(f)

        # Filter and return deals
        deals = []
        for deal in all_deals:
            if deal.get('status') == 'ACTIVE':
                # Ensure numeric fields are properly formatted
                deal['entry_price'] = float(deal.get('entry_price', 0))
                deal['current_price'] = float(deal.get('current_price', 0))
                deal['invested_amount'] = float(deal.get('invested_amount', 0))
                deal['current_value'] = float(deal.get('current_value', 0))
                deal['pnl_amount'] = float(deal.get('pnl_amount', 0))
                deal['pnl_percent'] = float(deal.get('pnl_percent', 0))
                deals.append(deal)
        
        logger.info(f"✓ Fetched {len(deals)} user deals from local storage")
        return deals

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        return []
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
        
        # Helper function to safely convert values
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
        
        # Set user_id early in the function - handle both string and integer user_ids safely
        session_user_id = session.get('user_id', 1)
        
        # Convert user_id to integer safely, fallback to 1 if invalid
        try:
            if isinstance(session_user_id, str):
                # If it's a string that's not numeric, use default user_id = 1
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

        # Additional validation
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

        # Use local JSON file storage instead of PostgreSQL
        deals_file = 'user_deals.json'
        
        # Ensure user_id is positive
        if not user_id or user_id <= 0:
            user_id = 1

        try:
            # Load existing deals or create new file
            if os.path.exists(deals_file):
                with open(deals_file, 'r') as f:
                    all_deals = json.load(f)
            else:
                all_deals = []

            # Create new deal record
            deal_id = len(all_deals) + 1
            new_deal = {
                'id': deal_id,
                'user_id': user_id,
                'symbol': symbol.upper(),
                'trading_symbol': symbol.upper(),
                'entry_date': datetime.now().strftime('%Y-%m-%d'),
                'position_type': 'LONG' if pos == 1 else 'SHORT',
                'quantity': qty,
                'entry_price': float(ep),
                'current_price': float(cmp),
                'target_price': float(tp),
                'stop_loss': float(ep * 0.95),  # Default 5% stop loss
                'invested_amount': float(invested_amount),
                'current_value': float(current_value),
                'pnl_amount': float(pnl_amount),
                'pnl_percent': float(pnl_percent),
                'status': 'ACTIVE',
                'deal_type': 'SIGNAL',
                'notes': f'Added from ETF signal - {symbol}',
                'tags': 'ETF,SIGNAL',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            all_deals.append(new_deal)

            # Save to JSON file
            with open(deals_file, 'w') as f:
                json.dump(all_deals, f, indent=2)

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
                # Check if users table exists and ensure user_id exists
                try:
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if not cursor.fetchone():
                        # Insert default user with the required ID
                        cursor.execute("""
                            INSERT INTO users (id, ucc, mobile_number, greeting_name, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (user_id, f'USER_{user_id}', '9999999999', f'User {user_id}', True))
                        conn.commit()
                        logger.info(f"Created default user with ID {user_id}")
                except Exception as user_check_error:
                    logger.warning(f"Could not verify/create user: {user_check_error}")
                    # Reset connection to clear any transaction issues
                    conn.rollback()
                    # Use default user_id = 1 and ensure it exists
                    user_id = 1
                    try:
                        cursor.execute("""
                            INSERT INTO users (id, ucc, mobile_number, greeting_name, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (1, 'DEFAULT_USER', '9999999999', 'Default User', True))
                        conn.commit()
                        logger.info("Created fallback default user with ID 1")
                    except Exception as fallback_error:
                        logger.error(f"Failed to create fallback user: {fallback_error}")
                        conn.rollback()

                # Insert into user_deals table
                insert_query = """
                    INSERT INTO user_deals (
                        user_id, symbol, trading_symbol, entry_date, position_type, quantity, entry_price,
                        current_price, target_price, stop_loss, invested_amount,
                        current_value, pnl_amount, pnl_percent, status, deal_type,
                        notes, tags, created_at, updated_at,
                        pos, qty, ep, cmp, tp, inv, pl
                    ) VALUES (
                        %s, %s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(),
                        %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """
                
                values = (
                    user_id,
                    symbol.upper(),
                    symbol.upper(),  # trading_symbol
                    'LONG' if pos == 1 else 'SHORT',
                    qty,
                    ep,
                    cmp,
                    tp,
                    ep * 0.95,  # Default 5% stop loss
                    invested_amount,
                    current_value,
                    pnl_amount,
                    pnl_percent,
                    'ACTIVE',
                    'SIGNAL',
                    f'Added from ETF signal - {symbol}',
                    'ETF,SIGNAL',
                    pos,
                    qty,
                    ep,
                    cmp,
                    tp,
                    invested_amount,
                    pnl_amount
                )

                logger.info(f"Executing insert query with values: {values}")
                cursor.execute(insert_query, values)
                
                # Get the deal ID
                result = cursor.fetchone()
                if not result or not result[0]:
                    raise Exception("Failed to create deal - no ID returned")
                
                deal_id = result[0]
                logger.info(f"Deal created with ID: {deal_id}")
                
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
            logger.error(f"Signal data was: {signal_data}")
            logger.error(f"Processed values were: user_id={user_id}, symbol={symbol}, qty={qty}, ep={ep}, cmp={cmp}")
            if conn:
                conn.rollback()
            
            # More specific error message
            error_msg = str(db_error)
            if not error_msg or error_msg == '0':
                error_msg = "Database insert failed - check signal data format"
            
            return jsonify({
                'success': False,
                'error': f'Failed to create deal: {error_msg}'
            }), 500
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logger.error(f"Error creating deal from signal: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500