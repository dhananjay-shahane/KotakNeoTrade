"""Admin Trade Signals API for ETF Signals page integration"""
from flask import request, jsonify, session, Blueprint
from app import db
from scripts.models_etf import AdminTradeSignal, KotakNeoQuote, RealtimeQuote
from scripts.models import User
from datetime import datetime
import logging

admin_signals_bp = Blueprint('admin_signals_api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@admin_signals_bp.route('/admin-trade-signals', methods=['GET'])
def get_admin_trade_signals():
    """Fetch admin trade signals with real-time market data for ETF signals page"""
    try:
        # Get all active admin trade signals
        signals = AdminTradeSignal.query.filter_by(status='ACTIVE').order_by(
            AdminTradeSignal.created_at.desc()
        ).all()
        
        if not signals:
            logger.info("No admin trade signals found, creating sample data...")
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No admin trade signals found',
                'total_count': 0
            })
        
        # Get comprehensive market data for all signal symbols
        signal_symbols = [signal.symbol for signal in signals]
        
        # Fetch from KotakNeoQuote first
        kotak_quotes = {}
        if signal_symbols:
            kotak_data = db.session.query(KotakNeoQuote).filter(
                KotakNeoQuote.symbol.in_(signal_symbols)
            ).order_by(KotakNeoQuote.timestamp.desc()).all()
            
            for quote in kotak_data:
                if quote.symbol not in kotak_quotes:
                    kotak_quotes[quote.symbol] = quote
        
        # Fallback to RealtimeQuote for missing symbols
        missing_symbols = [s for s in signal_symbols if s not in kotak_quotes]
        realtime_quotes = {}
        if missing_symbols:
            realtime_data = db.session.query(RealtimeQuote).filter(
                RealtimeQuote.symbol.in_(missing_symbols)
            ).order_by(RealtimeQuote.timestamp.desc()).all()
            
            for quote in realtime_data:
                if quote.symbol not in realtime_quotes:
                    realtime_quotes[quote.symbol] = quote
        
        signals_data = []
        total_investment = 0
        total_current_value = 0
        total_pnl = 0
        
        for signal in signals:
            # Get comprehensive market data
            kotak_quote = kotak_quotes.get(signal.symbol)
            realtime_quote = realtime_quotes.get(signal.symbol)
            
            # Determine current price and market data
            if kotak_quote:
                current_price = float(kotak_quote.ltp)
                open_price = float(kotak_quote.open_price) if kotak_quote.open_price else current_price
                high_price = float(kotak_quote.high_price) if kotak_quote.high_price else current_price
                low_price = float(kotak_quote.low_price) if kotak_quote.low_price else current_price
                change_percent = float(kotak_quote.percentage_change) if kotak_quote.percentage_change else 0
                volume = kotak_quote.volume or 0
                bid_price = float(kotak_quote.bid_price) if kotak_quote.bid_price else 0
                ask_price = float(kotak_quote.ask_price) if kotak_quote.ask_price else 0
                week_52_high = float(kotak_quote.week_52_high) if kotak_quote.week_52_high else 0
                week_52_low = float(kotak_quote.week_52_low) if kotak_quote.week_52_low else 0
                data_source = 'KOTAK_NEO_API'
                last_update = kotak_quote.timestamp
            elif realtime_quote:
                current_price = float(realtime_quote.current_price)
                open_price = float(realtime_quote.open_price) if realtime_quote.open_price else current_price
                high_price = float(realtime_quote.high_price) if realtime_quote.high_price else current_price
                low_price = float(realtime_quote.low_price) if realtime_quote.low_price else current_price
                change_percent = float(realtime_quote.change_percent) if realtime_quote.change_percent else 0
                volume = realtime_quote.volume or 0
                bid_price = ask_price = week_52_high = week_52_low = 0
                data_source = 'REALTIME_QUOTES'
                last_update = realtime_quote.timestamp
            else:
                # Fallback to signal data
                current_price = float(signal.current_price) if signal.current_price else float(signal.entry_price)
                open_price = high_price = low_price = current_price
                change_percent = 0
                volume = bid_price = ask_price = week_52_high = week_52_low = 0
                data_source = 'SIGNAL_DATA'
                last_update = signal.last_update_time or signal.updated_at
            
            # Calculate financial metrics
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            target_price = float(signal.target_price) if signal.target_price else 0
            stop_loss = float(signal.stop_loss) if signal.stop_loss else 0
            quantity = signal.quantity
            
            investment = entry_price * quantity
            current_value = current_price * quantity
            
            # Calculate P&L based on signal type
            if signal.signal_type == 'BUY':
                pnl = (current_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - current_price) * quantity
            
            pnl_percent = (pnl / investment * 100) if investment > 0 else 0
            
            # Day performance
            day_change = current_price - open_price
            day_change_percent = (day_change / open_price * 100) if open_price > 0 else 0
            
            # Get user information
            admin_user = User.query.get(signal.admin_user_id) if signal.admin_user_id else None
            target_user = User.query.get(signal.target_user_id) if signal.target_user_id else None
            
            signal_data = {
                'id': signal.id,
                'symbol': signal.symbol,
                'trading_symbol': signal.trading_symbol or signal.symbol,
                'token': signal.token,
                'exchange': signal.exchange,
                'signal_type': signal.signal_type,
                'status': signal.status,
                'priority': signal.priority,
                
                # Price data
                'entry_price': round(entry_price, 2),
                'current_price': round(current_price, 2),
                'target_price': round(target_price, 2),
                'stop_loss': round(stop_loss, 2),
                
                # Position data
                'quantity': quantity,
                'investment': round(investment, 2),
                'current_value': round(current_value, 2),
                'pnl': round(pnl, 2),
                'pnl_percent': round(pnl_percent, 2),
                
                # Market data
                'open_price': round(open_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'change_percent': round(change_percent, 2),
                'day_change': round(day_change, 2),
                'day_change_percent': round(day_change_percent, 2),
                'volume': volume,
                'bid_price': round(bid_price, 2),
                'ask_price': round(ask_price, 2),
                'week_52_high': round(week_52_high, 2),
                'week_52_low': round(week_52_low, 2),
                
                # Signal metadata
                'signal_title': signal.signal_title,
                'signal_description': signal.signal_description,
                'notes': signal.notes,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'expires_at': signal.expires_at.isoformat() if signal.expires_at else None,
                'last_update': last_update.isoformat() if last_update else None,
                'data_source': data_source,
                
                # User information
                'admin_user': {
                    'id': admin_user.id if admin_user else None,
                    'ucc': admin_user.ucc if admin_user else None,
                    'greeting_name': admin_user.greeting_name if admin_user else None
                },
                'target_user': {
                    'id': target_user.id if target_user else None,
                    'ucc': target_user.ucc if target_user else None,
                    'greeting_name': target_user.greeting_name if target_user else None
                },
                
                # Display formatting for DataTable
                'display_price': f"₹{current_price:.2f}",
                'display_change': f"{day_change_percent:+.2f}%",
                'display_pnl': f"₹{pnl:+,.2f}",
                'display_volume': f"{volume:,}" if volume > 0 else "N/A",
                'status_badge': signal.status.lower(),
                'signal_type_badge': signal.signal_type.lower()
            }
            
            signals_data.append(signal_data)
            total_investment += investment
            total_current_value += current_value
            total_pnl += pnl
        
        # Portfolio summary
        portfolio_summary = {
            'total_signals': len(signals_data),
            'total_investment': round(total_investment, 2),
            'total_current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round((total_pnl / total_investment * 100) if total_investment > 0 else 0, 2),
            'active_signals': len([s for s in signals_data if s['status'] == 'ACTIVE']),
            'buy_signals': len([s for s in signals_data if s['signal_type'] == 'BUY']),
            'sell_signals': len([s for s in signals_data if s['signal_type'] == 'SELL'])
        }
        
        # Sort by P&L descending (best performers first)
        signals_data.sort(key=lambda x: x['pnl'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': signals_data,
            'portfolio_summary': portfolio_summary,
            'data_sources': {
                'kotak_neo_quotes': len([s for s in signals_data if s['data_source'] == 'KOTAK_NEO_API']),
                'realtime_quotes': len([s for s in signals_data if s['data_source'] == 'REALTIME_QUOTES']),
                'signal_data': len([s for s in signals_data if s['data_source'] == 'SIGNAL_DATA'])
            },
            'total_count': len(signals_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Admin Trade Signals API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error fetching admin trade signals'
        }), 500

@admin_signals_bp.route('/admin-trade-signals/<int:signal_id>', methods=['GET'])
def get_admin_signal_detail(signal_id):
    """Get detailed information for a specific admin trade signal"""
    try:
        signal = AdminTradeSignal.query.get_or_404(signal_id)
        
        # Get latest market data
        kotak_quote = KotakNeoQuote.query.filter_by(symbol=signal.symbol).order_by(
            KotakNeoQuote.timestamp.desc()
        ).first()
        
        realtime_quote = RealtimeQuote.query.filter_by(symbol=signal.symbol).order_by(
            RealtimeQuote.timestamp.desc()
        ).first()
        
        # Build detailed response
        detail_data = signal.to_dict()
        
        if kotak_quote:
            detail_data['market_data'] = kotak_quote.to_dict()
        elif realtime_quote:
            detail_data['market_data'] = realtime_quote.to_dict()
        
        return jsonify({
            'success': True,
            'data': detail_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Admin Signal Detail API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500