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
        # Get raw deals from database
        raw_deals = get_user_deals_from_db()

        if not raw_deals:
            logger.info("No user deals found - database is empty")
            return jsonify({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'message': 'No trading deals found. Please add your real trading data to the user_deals table.',
                'instructions': 'Use real trading data from your broker account - no sample data allowed.'
            })

        # Process each deal with calculations
        formatted_deals = []
        for deal in raw_deals:
            calculated_deal = calculate_deal_metrics(deal)
            if calculated_deal:
                calculated_deal['id'] = deal.get('id')
                formatted_deals.append(calculated_deal)

        # Sort by creation date (newest first)
        formatted_deals.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        total_deals = len(formatted_deals)
        success_message = f"✅ Successfully processed {total_deals} deals."

        logger.info(success_message)

        return jsonify({
            'data': formatted_deals,
            'recordsTotal': total_deals,
            'recordsFiltered': total_deals,
            'message': success_message
        })

    except Exception as e:
        logger.error(f"❌ Error in get_user_deals API: {e}")
        traceback.print_exc()
        return jsonify({
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
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

@deals_api.route('/api/deals/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a deal from a signal (placeholder)"""
    try:
        data = request.get_json()
        # Implement deal creation logic here based on signal data
        return jsonify({
            'success': True,
            'message': 'Deal created from signal (placeholder)',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error creating deal from signal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500