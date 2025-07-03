"""
Direct Datatable Updates API for admin_trade_signals
Provides real-time price updates from Yahoo Finance and Google Finance
"""
from flask import Blueprint, jsonify, request, session
from app import db
from Scripts.models_etf import AdminTradeSignal
from Scripts.yahoo_finance_service import YahooFinanceService
from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
import logging

datatable_updates_bp = Blueprint('datatable_updates', __name__, url_prefix='/api/datatable')
logger = logging.getLogger(__name__)

@datatable_updates_bp.route('/update-prices/<source>', methods=['POST'])
def update_datatable_prices(source):
    """Update datatable prices directly from selected source (yahoo/google)"""
    try:
        # Allow unauthenticated access for price updates
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Authentication required'}), 401

        # Get optional symbol list from request (handle both JSON and form data)
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        symbol_list = data.get('symbols', [])
        
        if source.lower() == 'yahoo':
            return update_from_yahoo_finance(symbol_list)
        elif source.lower() == 'google':
            return update_from_google_finance(symbol_list)
        else:
            return jsonify({
                'success': False,
                'error': f'Invalid price source: {source}. Use "yahoo" or "google"'
            }), 400

    except Exception as e:
        logger.error(f"Error updating datatable prices from {source}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def update_from_yahoo_finance(symbol_list=None):
    """Update prices using Yahoo Finance service"""
    try:
        yahoo_service = YahooFinanceService()
        
        if symbol_list:
            # Update specific symbols
            result = yahoo_service.update_specific_symbols(symbol_list)
        else:
            # Update all symbols
            result = yahoo_service.update_all_symbols()
        
        if result['status'] == 'success':
            # Get updated data for datatable refresh
            updated_data = get_updated_datatable_data(result.get('updates', []))
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated {result["successful_updates"]} symbols via Yahoo Finance',
                'data_source': 'Yahoo Finance',
                'total_symbols': result['total_symbols'],
                'successful_updates': result['successful_updates'],
                'failed_updates': result['failed_updates'],
                'updated_data': updated_data,
                'timestamp': result.get('timestamp', ''),
                'details': result.get('updates', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error from Yahoo Finance'),
                'data_source': 'Yahoo Finance'
            }), 500
            
    except Exception as e:
        logger.error(f"Yahoo Finance update error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data_source': 'Yahoo Finance'
        }), 500

def update_from_google_finance(symbol_list=None):
    """Update prices using Google Finance service"""
    try:
        # Use the external database connection string
        db_connection = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"
        google_service = GoogleFinanceCMPUpdater(db_connection)
        
        if symbol_list:
            # Update specific symbols
            result = google_service.update_specific_symbols(symbol_list)
        else:
            # Update all symbols
            result = google_service.update_all_symbols()
        
        if result['status'] == 'success':
            # Get updated data for datatable refresh
            updated_data = get_updated_datatable_data(result.get('updates', []))
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated {result["successful_updates"]} symbols via Google Finance',
                'data_source': 'Google Finance',
                'total_symbols': result['total_symbols'],
                'successful_updates': result['successful_updates'],
                'failed_updates': result['failed_updates'],
                'updated_data': updated_data,
                'timestamp': result.get('timestamp', ''),
                'details': result.get('updates', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error from Google Finance'),
                'data_source': 'Google Finance'
            }), 500
            
    except Exception as e:
        logger.error(f"Google Finance update error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data_source': 'Google Finance'
        }), 500

def get_updated_datatable_data(updates):
    """Get formatted datatable data for updated symbols"""
    try:
        updated_symbols = [update['symbol'] for update in updates if update.get('status') == 'success']
        
        if not updated_symbols:
            return []
        
        # Query updated signals
        signals = AdminTradeSignal.query.filter(
            AdminTradeSignal.symbol.in_(updated_symbols)
        ).all()
        
        formatted_data = []
        for signal in signals:
            # Calculate P&L and other metrics
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            current_price = float(signal.current_price) if signal.current_price else 0
            quantity = signal.quantity or 0
            
            investment = entry_price * quantity
            current_value = current_price * quantity
            pnl_amount = current_value - investment
            pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            formatted_data.append({
                'id': signal.id,
                'symbol': signal.symbol,
                'entry_price': entry_price,
                'current_price': current_price,
                'quantity': quantity,
                'investment': investment,
                'current_value': current_value,
                'pnl_amount': pnl_amount,
                'pnl_percent': pnl_percent,
                'last_updated': signal.last_update_time.isoformat() if signal.last_update_time else None,
                'formatted': {
                    'entry_price': f"₹{entry_price:,.2f}",
                    'current_price': f"₹{current_price:,.2f}",
                    'investment': f"₹{investment:,.2f}",
                    'current_value': f"₹{current_value:,.2f}",
                    'pnl_amount': f"₹{pnl_amount:,.2f}",
                    'pnl_percent': f"{pnl_percent:+.2f}%"
                }
            })
        
        return formatted_data
        
    except Exception as e:
        logger.error(f"Error formatting datatable data: {e}")
        return []

@datatable_updates_bp.route('/refresh-data', methods=['POST'])
def refresh_datatable_data():
    """Refresh datatable data without price updates"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get all admin trade signals
        signals = AdminTradeSignal.query.order_by(AdminTradeSignal.created_at.desc()).all()
        
        formatted_data = []
        for signal in signals:
            # Calculate metrics
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            current_price = float(signal.current_price) if signal.current_price else 0
            quantity = signal.quantity or 0

            investment = entry_price * quantity
            current_value = current_price * quantity
            pnl_amount = current_value - investment
            pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

            formatted_data.append({
                'id': signal.id,
                'symbol': signal.symbol,
                'trading_symbol': signal.trading_symbol,
                'signal_type': signal.signal_type,
                'entry_price': entry_price,
                'current_price': current_price,
                'quantity': quantity,
                'investment': investment,
                'current_value': current_value,
                'pnl_amount': pnl_amount,
                'pnl_percent': pnl_percent,
                'status': signal.status,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'last_updated': signal.last_update_time.isoformat() if signal.last_update_time else None,
                'formatted': {
                    'entry_price': f"₹{entry_price:,.2f}",
                    'current_price': f"₹{current_price:,.2f}",
                    'investment': f"₹{investment:,.2f}",
                    'current_value': f"₹{current_value:,.2f}",
                    'pnl_amount': f"₹{pnl_amount:,.2f}",
                    'pnl_percent': f"{pnl_percent:+.2f}%"
                }
            })

        return jsonify({
            'success': True,
            'message': f'Refreshed data for {len(formatted_data)} signals',
            'total_records': len(formatted_data),
            'data': formatted_data
        })

    except Exception as e:
        logger.error(f"Error refreshing datatable data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@datatable_updates_bp.route('/refresh-performance-data', methods=['POST'])
def refresh_performance_data():
    """Refresh datatable data with latest performance metrics"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info("🔄 Refreshing datatable with latest performance data")
        
        # Import here to avoid circular imports
        from Scripts.external_db_service import get_etf_signals_data_json
        
        # Get fresh data from external database
        fresh_data = get_etf_signals_data_json()
        
        if 'error' in fresh_data:
            return jsonify({
                'success': False,
                'message': f"Error refreshing data: {fresh_data['error']}"
            }), 500
        
        # Count records with performance data
        performance_count = 0
        for record in fresh_data['data']:
            if record.get('d30', 0) > 0 or record.get('d7', 0) > 0:
                performance_count += 1
        
        logger.info(f"✅ Refreshed {fresh_data['recordsTotal']} records, {performance_count} with performance data")
        
        return jsonify({
            'success': True,
            'message': f'Refreshed {fresh_data["recordsTotal"]} records with latest performance data',
            'data': fresh_data['data'],
            'recordsTotal': fresh_data['recordsTotal'],
            'recordsFiltered': fresh_data['recordsFiltered'],
            'performance_records': performance_count
        })
        
    except Exception as e:
        logger.error(f"❌ Error refreshing performance data: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to refresh performance data'
        }), 500

@datatable_updates_bp.route('/force-performance-update', methods=['POST'])
def force_performance_update():
    """Force update performance data and refresh datatable"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info("🚀 Force updating performance data...")
        
        # Import performance calculator
        from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
        
        # Update performance data
        updater = GoogleFinanceCMPUpdater()
        result = updater.update_all_symbols()
        
        if result.get('success'):
            # Get refreshed datatable data
            from Scripts.external_db_service import get_etf_signals_data_json
            fresh_data = get_etf_signals_data_json()
            
            return jsonify({
                'success': True,
                'message': f'Updated {result.get("updated_count", 0)} records with performance data',
                'data': fresh_data['data'],
                'recordsTotal': fresh_data['recordsTotal'],
                'update_details': {
                    'symbols_processed': result.get('total_symbols', 0),
                    'successful_updates': result.get('successful_symbols', 0),
                    'database_rows_updated': result.get('updated_count', 0),
                    'duration': result.get('duration', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Performance update failed: {result.get("message", "Unknown error")}'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error in force performance update: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to force update performance data'
        }), 500

@datatable_updates_bp.route('/symbols', methods=['GET'])
def get_available_symbols():
    """Get all available symbols in admin_trade_signals"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        symbols = db.session.query(AdminTradeSignal.symbol).distinct().filter(
            AdminTradeSignal.symbol.isnot(None)
        ).all()
        
        symbol_list = [s[0] for s in symbols]
        
        return jsonify({
            'success': True,
            'symbols': symbol_list,
            'total_symbols': len(symbol_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500