"""Enhanced ETF Signals API with comprehensive Kotak Neo quotes integration"""
from flask import request, jsonify, session, Blueprint
from app import db
from Scripts.models_etf import KotakNeoQuote, AdminTradeSignal, RealtimeQuote
from Scripts.models import User
from Scripts.trading_functions import TradingFunctions
from datetime import datetime
import logging

enhanced_etf_bp = Blueprint('enhanced_etf', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@enhanced_etf_bp.route('/enhanced-etf-signals', methods=['GET'])
def get_enhanced_etf_signals():
    """Get comprehensive ETF signals with Kotak Neo quotes data and real-time CMP values"""
    try:
        # ETF symbols and their market data
        etf_symbols = [
            'NIFTYBEES', 'BANKBEES', 'LIQUIDBEES', 'GOLDSHARE', 'ITBEES',
            'JUNIORBEES', 'HDFCNIFTY', 'ICICINIFTY', 'RELGOLD', 'HDFCGOLD',
            'AXISGOLD', 'KOTAKSILV', 'KOTAKNV20', 'KOTAKPSU', 'PSUBNKBEES',
            'ICICIB22', 'ICICIPRUH', 'ICICINXT50', 'AXISBNK'
        ]
        
        # Get comprehensive quotes from KotakNeoQuote table
        comprehensive_quotes = {}
        kotak_quotes = db.session.query(KotakNeoQuote).filter(
            KotakNeoQuote.symbol.in_(etf_symbols)
        ).order_by(KotakNeoQuote.timestamp.desc()).all()
        
        # Group by symbol and get latest
        for quote in kotak_quotes:
            if quote.symbol not in comprehensive_quotes:
                comprehensive_quotes[quote.symbol] = quote.to_dict()
        
        # Fallback to RealtimeQuote for missing symbols
        missing_symbols = [s for s in etf_symbols if s not in comprehensive_quotes]
        if missing_symbols:
            realtime_quotes = db.session.query(RealtimeQuote).filter(
                RealtimeQuote.symbol.in_(missing_symbols)
            ).order_by(RealtimeQuote.timestamp.desc()).all()
            
            for quote in realtime_quotes:
                if quote.symbol not in comprehensive_quotes:
                    comprehensive_quotes[quote.symbol] = {
                        'symbol': quote.symbol,
                        'ltp': float(quote.current_price),
                        'open_price': float(quote.open_price) if quote.open_price else float(quote.current_price),
                        'high_price': float(quote.high_price) if quote.high_price else float(quote.current_price),
                        'low_price': float(quote.low_price) if quote.low_price else float(quote.current_price),
                        'percentage_change': float(quote.change_percent) if quote.change_percent else 0,
                        'volume': quote.volume or 0,
                        'data_source': 'REALTIME_QUOTES',
                        'timestamp': quote.timestamp.isoformat() if quote.timestamp else None
                    }
        
        # Get admin trade signals
        admin_signals = AdminTradeSignal.query.filter_by(status='ACTIVE').limit(50).all()
        
        enhanced_signals = []
        total_investment = 0
        total_current_value = 0
        total_pnl = 0
        
        # Process each admin signal with comprehensive market data
        for signal in admin_signals:
            quote_data = comprehensive_quotes.get(signal.symbol, {})
            
            # Current market price from comprehensive data
            current_price = float(quote_data.get('ltp', signal.current_price or signal.entry_price))
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            quantity = signal.quantity
            
            # Calculate comprehensive metrics
            investment = entry_price * quantity
            current_value = current_price * quantity
            pnl = (current_price - entry_price) * quantity if entry_price > 0 else 0
            pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            # Day performance
            open_price = float(quote_data.get('open_price', current_price))
            day_change = current_price - open_price
            day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
            
            enhanced_signal = {
                'id': signal.id,
                'symbol': signal.symbol,
                'trading_symbol': signal.trading_symbol or signal.symbol,
                'signal_type': signal.signal_type,
                'status': signal.status,
                'priority': signal.priority,
                
                # Price data
                'entry_price': round(entry_price, 2),
                'current_price': round(current_price, 2),
                'target_price': float(signal.target_price) if signal.target_price else 0,
                'stop_loss': float(signal.stop_loss) if signal.stop_loss else 0,
                
                # Position data
                'quantity': quantity,
                'investment': round(investment, 2),
                'current_value': round(current_value, 2),
                'pnl': round(pnl, 2),
                'pnl_percent': round(pnl_percent, 2),
                
                # Market data from Kotak Neo API
                'open_price': round(open_price, 2),
                'high_price': round(float(quote_data.get('high_price', current_price)), 2),
                'low_price': round(float(quote_data.get('low_price', current_price)), 2),
                'day_change': round(day_change, 2),
                'day_change_percent': round(day_change_percent, 2),
                'volume': quote_data.get('volume', 0),
                'bid_price': round(float(quote_data.get('bid_price', 0)), 2),
                'ask_price': round(float(quote_data.get('ask_price', 0)), 2),
                'week_52_high': round(float(quote_data.get('week_52_high', 0)), 2),
                'week_52_low': round(float(quote_data.get('week_52_low', 0)), 2),
                
                # Metadata
                'signal_title': signal.signal_title,
                'signal_description': signal.signal_description,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'data_source': quote_data.get('data_source', 'ADMIN_SIGNAL'),
                'last_update': quote_data.get('timestamp') or (signal.last_update_time.isoformat() if signal.last_update_time else None),
                
                # Display formatting
                'display_price': f"₹{current_price:.2f}",
                'display_change': f"{day_change_percent:+.2f}%",
                'display_pnl': f"₹{pnl:+,.2f}",
                'display_volume': f"{quote_data.get('volume', 0):,}" if quote_data.get('volume', 0) > 0 else "N/A"
            }
            
            enhanced_signals.append(enhanced_signal)
            total_investment += investment
            total_current_value += current_value
            total_pnl += pnl
        
        # Portfolio summary
        portfolio_summary = {
            'total_signals': len(enhanced_signals),
            'total_investment': round(total_investment, 2),
            'total_current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round((total_pnl / total_investment * 100) if total_investment > 0 else 0, 2),
            'active_signals': len([s for s in enhanced_signals if s['status'] == 'ACTIVE'])
        }
        
        # Sort by PnL descending
        enhanced_signals.sort(key=lambda x: x['pnl'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': enhanced_signals,
            'portfolio_summary': portfolio_summary,
            'market_data_sources': {
                'kotak_neo_quotes': len([s for s in enhanced_signals if s['data_source'] == 'KOTAK_NEO_API']),
                'realtime_quotes': len([s for s in enhanced_signals if s['data_source'] == 'REALTIME_QUOTES']),
                'admin_signals': len([s for s in enhanced_signals if s['data_source'] == 'ADMIN_SIGNAL'])
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Enhanced ETF Signals API Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_etf_bp.route('/market-overview', methods=['GET'])
def get_market_overview():
    """Get comprehensive market overview from KotakNeoQuote data"""
    try:
        # Get latest quotes for all ETF symbols
        latest_quotes = db.session.query(KotakNeoQuote).order_by(
            KotakNeoQuote.timestamp.desc()
        ).limit(50).all()
        
        market_data = []
        for quote in latest_quotes:
            market_data.append({
                'symbol': quote.symbol,
                'ltp': float(quote.ltp),
                'change_percent': float(quote.percentage_change) if quote.percentage_change else 0,
                'volume': quote.volume or 0,
                'high_price': float(quote.high_price) if quote.high_price else float(quote.ltp),
                'low_price': float(quote.low_price) if quote.low_price else float(quote.ltp),
                'market_status': quote.market_status,
                'last_update': quote.timestamp.isoformat() if quote.timestamp else None
            })
        
        # Calculate market statistics
        gainers = [q for q in market_data if q['change_percent'] > 0]
        losers = [q for q in market_data if q['change_percent'] < 0]
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'statistics': {
                'total_symbols': len(market_data),
                'gainers': len(gainers),
                'losers': len(losers),
                'unchanged': len(market_data) - len(gainers) - len(losers),
                'top_gainer': max(gainers, key=lambda x: x['change_percent']) if gainers else None,
                'top_loser': min(losers, key=lambda x: x['change_percent']) if losers else None
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Market Overview API Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500