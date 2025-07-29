"""
This commit addresses the issue of undefined value errors in the loadSymbolData function by adding null checks and error handling, and ensures the API returns proper data structure for deals.
"""
import logging
from flask import Blueprint, jsonify, session
from Scripts.user_deals_service import UserDealsService

logger = logging.getLogger(__name__)

# Create blueprint for portfolio API
portfolio_api = Blueprint('portfolio_api', __name__)

# Initialize user deals service
user_deals_service = UserDealsService()


@portfolio_api.route('/api/portfolio/stats')
def get_portfolio_stats():
    """Get portfolio statistics for dashboard cards and charts"""
    try:
        # Get user ID from session
        user_id = session.get('user_id', 1)

        logger.info(f"Fetching portfolio stats for user_id: {user_id}")

        # Fetch deals statistics
        deals_stats = user_deals_service.get_deals_statistics(user_id)

        logger.info(f"Portfolio stats result: {deals_stats}")

        return jsonify({
            'success': True,
            'data': deals_stats
        })

    except Exception as e:
        logger.error(f"Error fetching portfolio stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'total_deals': 0,
                'active_deals': 0,
                'closed_deals': 0,
                'symbols': [],
                'symbol_chart_data': {'labels': [], 'data': [], 'colors': []},
                'status_chart_data': {'labels': [], 'data': [], 'colors': []},
                'deals_list': []
            }
        })


@portfolio_api.route('/api/portfolio/symbols')
def get_portfolio_symbols():
    """Get list of symbols from user deals"""
    try:
        user_id = session.get('user_id', 1)
        deals_stats = user_deals_service.get_deals_statistics(user_id)

        return jsonify({
            'success': True,
            'data': deals_stats.get('symbols', [])
        })

    except Exception as e:
        logger.error(f"Error fetching portfolio symbols: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        })


@portfolio_api.route('/api/portfolio/symbol-data/<symbol>')
def get_symbol_data(symbol):
    """Get detailed data for a specific symbol"""
    try:
        user_id = session.get('user_id', 1)

        # Get symbol-specific details (CMP, investment, P/L)
        symbol_details = user_deals_service.get_symbol_details(user_id, symbol)

        if not symbol_details:
            return jsonify({
                'success': False,
                'error': f"No details found for symbol {symbol}",
                'data': {}
            })

        cmp = symbol_details.get('cmp', 0)
        total_investment = symbol_details.get('total_investment', 0)
        current_value = symbol_details.get('current_value', 0)
        profit_loss = symbol_details.get('profit_loss', 0)
        profit_loss_pct = symbol_details.get('profit_loss_percentage', 0)

        # Get deals for this symbol
        deals = user_deals_service.get_deals_by_symbol(user_id, symbol)

        # Calculate current values and prepare deals data
        deals_data = []
        if deals and isinstance(deals, list):
            for deal in deals:
                try:
                    entry_price = float(deal.get('ep', 0)) if deal.get('ep') else 0
                    qty = int(deal.get('qty', 0)) if deal.get('qty') else 0
                    current_value = entry_price * qty if entry_price and qty else 0

                    deals_data.append({
                        'date': deal.get('created_at').strftime('%Y-%m-%d') if deal.get('created_at') else 'N/A',
                        'entry_price': entry_price,
                        'qty': qty,
                        'investment': current_value,
                        'current_value': current_value,
                        'status': deal.get('status', 'Unknown')
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing deal data: {e}")
                    continue

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'cmp': cmp,
                'total_investment': total_investment,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_percentage': f"{profit_loss_pct:.2f}",
                'deals': deals_data if deals_data else []
            }
        })

    except Exception as e:
        logger.error(f"Error fetching symbol data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        })