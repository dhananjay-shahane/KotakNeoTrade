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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

deals_api = Blueprint('deals_api', __name__)

def get_user_deals_from_db():
    """
    Get user deals from external database (user_deals table)
    Returns all deals with proper structure for calculations
    """
    try:
        # Connect to external database
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to external database")
            return []
            
        with conn.cursor() as cursor:
            # Query to get all user deals with proper joins if needed
            query = """
            SELECT 
                id,
                symbol,
                date,
                pos,
                qty,
                ep,
                cmp,
                d30,
                d7,
                status,
                ed,
                exp,
                created_at,
                updated_at
            FROM user_deals 
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            deals = []
            
            for row in cursor.fetchall():
                deal = dict(zip(columns, row))
                deals.append(deal)
                
            logger.info(f"✓ Fetched {len(deals)} user deals from database")
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

        # Position: 1 for buy (long), -1 for sell (short)
        pos = int(deal.get('pos', 1))
        
        # Status: 1 for running deal, 0 for closed deal
        status = int(deal.get('status', 1))

        # Handle numeric fields with null safety
        qty = float(deal.get('qty', 0)) if deal.get('qty') is not None else 0.0
        ep = float(deal.get('ep', 0)) if deal.get('ep') is not None else 0.0
        cmp = float(deal.get('cmp', 0)) if deal.get('cmp') is not None else 0.0
        
        # Historical prices for 7-day and 30-day calculations
        d7_price = float(deal.get('d7', 0)) if deal.get('d7') is not None else 0.0
        d30_price = float(deal.get('d30', 0)) if deal.get('d30') is not None else 0.0

        # Calculate investment amount (qty * ep)
        inv = qty * ep if qty and ep else 0

        # Calculate current value and P&L
        current_value = qty * cmp if qty and cmp else 0
        
        # Calculate P&L based on position type
        if pos == 1:  # Long position (buy)
            pl = current_value - inv  # Profit/Loss
            chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
        else:  # Short position (sell)
            pl = inv - current_value  # Profit/Loss (reversed for short)
            chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0

        # Calculate 30-day and 7-day performance percentages
        ch30_percent = ((cmp - d30_price) / d30_price) * 100 if d30_price > 0 else 0
        ch7_percent = ((cmp - d7_price) / d7_price) * 100 if d7_price > 0 else 0

        # Calculate price changes
        ch30_value = cmp - d30_price if d30_price > 0 else 0
        ch7_value = cmp - d7_price if d7_price > 0 else 0
        chan_value = cmp - ep if ep > 0 else 0

        # Calculate target price (assume 3% target)
        target_percent = 3.0
        if pos == 1:  # Long position
            tp = ep * (1 + target_percent / 100)
        else:  # Short position
            tp = ep * (1 - target_percent / 100) if ep > 0 else 0

        # Calculate target value amount and target profit
        tva = qty * tp if qty and tp else 0
        tpr = tva - inv if pos == 1 else inv - tva

        # Handle exit data for closed deals
        ed = deal.get('ed', '')  # Exit date
        exp = deal.get('exp', '')  # Exit price

        # Calculate exit profit if exit price exists
        if exp and status == 0:  # Only for closed deals
            try:
                exp_value = float(exp)
                pr = (exp_value - ep) * qty if qty and ep else 0
                pp = (pr / inv * 100) if inv > 0 else 0
            except (ValueError, TypeError):
                pr = 0
                pp = 0
        else:
            pr = 0
            pp = 0

        return {
            'symbol': symbol,
            'date': deal.get('date', ''),
            'pos': pos,
            'status': status,
            'qty': int(qty),
            'ep': round(ep, 2),
            'cmp': round(cmp, 2),
            'inv': round(inv, 2),
            'current_value': round(current_value, 2),
            'pl': round(pl, 2),
            'chan_percent': f"{chan_percent:.2f}%",
            'chan_value': round(chan_value, 2),
            'd30_price': round(d30_price, 2),
            'd7_price': round(d7_price, 2),
            'ch30_percent': f"{ch30_percent:.2f}%",
            'ch7_percent': f"{ch7_percent:.2f}%",
            'ch30_value': round(ch30_value, 2),
            'ch7_value': round(ch7_value, 2),
            'tp': round(tp, 2),
            'tva': round(tva, 2),
            'tpr': round(tpr, 2),
            'ed': ed,
            'exp': exp,
            'pr': round(pr, 2),
            'pp': f"{pp:.2f}%",
            # Formatted display values
            'ep_formatted': f"₹{ep:.2f}",
            'cmp_formatted': f"₹{cmp:.2f}",
            'inv_formatted': f"₹{inv:.2f}",
            'pl_formatted': f"₹{pl:.2f}",
            'tp_formatted': f"₹{tp:.2f}",
            'tva_formatted': f"₹{tva:.2f}",
            'tpr_formatted': f"₹{tpr:.2f}",
            'created_at': deal.get('created_at', ''),
            'updated_at': deal.get('updated_at', '')
        }
        
    except Exception as e:
        logger.error(f"Error calculating metrics for deal {deal.get('id', 'unknown')}: {e}")
        return None

@deals_api.route('/api/user-deals', methods=['GET'])
@require_auth
def get_user_deals():
    """
    API endpoint to get user deals with all calculations
    Returns properly formatted data for DataTable
    """
    try:
        # Get raw deals from database
        raw_deals = get_user_deals_from_db()
        
        if not raw_deals:
            logger.warning("No deals found in database")
            return jsonify({
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'message': 'No deals found in database'
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

@deals_api.route('/api/deals-summary', methods=['GET'])
@require_auth
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

@deals_api.route('/api/deals/<int:deal_id>', methods=['GET'])
@require_auth
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