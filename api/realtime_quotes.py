"""
Real-time Quotes API endpoints
"""

from flask import Blueprint, jsonify, request, session
from app import db
from Scripts.models_etf import RealtimeQuote, ETFSignalTrade, AdminTradeSignal
from Scripts.realtime_quotes_manager import realtime_quotes_manager, get_latest_quotes_api, force_fetch_quotes
import logging
from datetime import datetime, timedelta

quotes_bp = Blueprint('quotes', __name__, url_prefix='/api/quotes')
logger = logging.getLogger(__name__)

@quotes_bp.route('/latest', methods=['GET'])
def get_latest_quotes():
    """Get latest quotes for specified symbols"""
    try:
        symbols = request.args.getlist('symbols')
        if not symbols:
            symbols = None
        
        quotes = get_latest_quotes_api(symbols)
        
        return jsonify({
            'success': True,
            'quotes': quotes,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting latest quotes: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching quotes: {str(e)}'
        }), 500

@quotes_bp.route('/symbols', methods=['GET'])
def get_tracked_symbols():
    """Get all symbols being tracked"""
    try:
        # Get unique symbols from active signals
        etf_symbols = db.session.query(ETFSignalTrade.symbol).filter(
            ETFSignalTrade.status == 'ACTIVE'
        ).distinct().all()
        
        admin_symbols = db.session.query(AdminTradeSignal.symbol).filter(
            AdminTradeSignal.status == 'ACTIVE'
        ).distinct().all()
        
        # Combine and format
        all_symbols = set()
        for symbol in etf_symbols:
            all_symbols.add(symbol[0])
        for symbol in admin_symbols:
            all_symbols.add(symbol[0])
        
        return jsonify({
            'success': True,
            'symbols': list(all_symbols),
            'count': len(all_symbols)
        })
        
    except Exception as e:
        logger.error(f"Error getting tracked symbols: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching symbols: {str(e)}'
        }), 500

@quotes_bp.route('/history/<symbol>', methods=['GET'])
def get_quote_history(symbol):
    """Get quote history for a symbol"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Calculate time range
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        quotes = RealtimeQuote.query.filter(
            RealtimeQuote.symbol == symbol,
            RealtimeQuote.timestamp >= start_time
        ).order_by(RealtimeQuote.timestamp.desc()).limit(limit).all()
        
        quote_data = [quote.to_dict() for quote in quotes]
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'quotes': quote_data,
            'count': len(quote_data),
            'timeframe': f'{hours} hours'
        })
        
    except Exception as e:
        logger.error(f"Error getting quote history for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching quote history: {str(e)}'
        }), 500

@quotes_bp.route('/force-update', methods=['POST'])
def force_quote_update():
    """Force an immediate quote update"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        
        success = force_fetch_quotes()
        
        return jsonify({
            'success': success,
            'message': 'Quote update completed' if success else 'Quote update failed',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error forcing quote update: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating quotes: {str(e)}'
        }), 500

@quotes_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        # Get latest quote timestamp
        latest_quote = RealtimeQuote.query.order_by(
            RealtimeQuote.timestamp.desc()
        ).first()
        
        # Get quote count for last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_count = RealtimeQuote.query.filter(
            RealtimeQuote.timestamp >= yesterday
        ).count()
        
        # Get unique symbols tracked
        unique_symbols = db.session.query(RealtimeQuote.symbol).distinct().count()
        
        return jsonify({
            'success': True,
            'scheduler_running': realtime_quotes_manager.is_running,
            'latest_update': latest_quote.timestamp.isoformat() if latest_quote else None,
            'quotes_last_24h': recent_count,
            'symbols_tracked': unique_symbols,
            'status': 'active' if realtime_quotes_manager.is_running else 'stopped'
        })
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting status: {str(e)}'
        }), 500

@quotes_bp.route('/statistics', methods=['GET'])
def get_quote_statistics():
    """Get detailed quote statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total quotes
        total_quotes = RealtimeQuote.query.filter(
            RealtimeQuote.timestamp >= start_date
        ).count()
        
        # Quotes per symbol
        symbol_stats = db.session.query(
            RealtimeQuote.symbol,
            db.func.count(RealtimeQuote.id).label('quote_count'),
            db.func.max(RealtimeQuote.timestamp).label('last_update'),
            db.func.avg(RealtimeQuote.current_price).label('avg_price')
        ).filter(
            RealtimeQuote.timestamp >= start_date
        ).group_by(RealtimeQuote.symbol).all()
        
        symbol_data = []
        for stat in symbol_stats:
            symbol_data.append({
                'symbol': stat.symbol,
                'quote_count': stat.quote_count,
                'last_update': stat.last_update.isoformat() if stat.last_update else None,
                'avg_price': float(stat.avg_price) if stat.avg_price else None
            })
        
        return jsonify({
            'success': True,
            'period_days': days,
            'total_quotes': total_quotes,
            'symbols_data': symbol_data,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting quote statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting statistics: {str(e)}'
        }), 500