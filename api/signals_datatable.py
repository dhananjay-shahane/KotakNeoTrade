"""
Analysis: The code modifies the get_admin_signals_datatable function to format the data according to the specified field names and structure.
"""
from flask import Blueprint, jsonify, request, session
from app import db
from scripts.models_etf import ETFSignalTrade, AdminTradeSignal, RealtimeQuote
from scripts.models import User
from sqlalchemy import and_, or_, desc, asc, text
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import logging
import math

datatable_bp = Blueprint('datatable', __name__, url_prefix='/api/datatable')
logger = logging.getLogger(__name__)

class DataTableProcessor:
    """Process DataTable requests with advanced features"""

    def __init__(self, model, base_query=None):
        self.model = model
        self.base_query = base_query or db.session.query(model)

    def process_request(self, request_data, searchable_columns=None, orderable_columns=None):
        """Process DataTable request and return formatted response"""
        try:
            # Extract DataTable parameters
            draw = int(request_data.get('draw', 1))
            start = int(request_data.get('start', 0))
            length = int(request_data.get('length', 10))
            search_value = request_data.get('search[value]', '').strip()

            # Start with base query
            query = self.base_query

            # Apply global search
            if search_value and searchable_columns:
                search_conditions = []
                for column in searchable_columns:
                    if hasattr(self.model, column):
                        attr = getattr(self.model, column)
                        search_conditions.append(
                            attr.ilike(f'%{search_value}%')
                        )

                if search_conditions:
                    query = query.filter(or_(*search_conditions))

            # Apply column-specific searches
            for i in range(20):  # Check up to 20 columns
                column_search = request_data.get(f'columns[{i}][search][value]', '').strip()
                column_name = request_data.get(f'columns[{i}][data]', '')

                if column_search and column_name and hasattr(self.model, column_name):
                    attr = getattr(self.model, column_name)
                    query = query.filter(attr.ilike(f'%{column_search}%'))

            # Apply ordering
            order_column_idx = request_data.get('order[0][column]')
            order_dir = request_data.get('order[0][dir]', 'asc')

            if order_column_idx and orderable_columns:
                try:
                    column_idx = int(order_column_idx)
                    if 0 <= column_idx < len(orderable_columns):
                        column_name = orderable_columns[column_idx]
                        if hasattr(self.model, column_name):
                            attr = getattr(self.model, column_name)
                            if order_dir == 'desc':
                                query = query.order_by(desc(attr))
                            else:
                                query = query.order_by(asc(attr))
                except (ValueError, IndexError):
                    pass

            # Get total count before pagination
            total_records = query.count()

            # Apply pagination
            query = query.offset(start).limit(length)

            # Execute query
            records = query.all()

            return {
                'draw': draw,
                'recordsTotal': db.session.query(self.model).count(),
                'recordsFiltered': total_records,
                'data': records
            }

        except Exception as e:
            logger.error(f"Error processing DataTable request: {str(e)}")
            return {
                'draw': draw,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': str(e)
            }

@datatable_bp.route('/etf-signals/user', methods=['POST'])
def get_user_etf_signals_datatable():
    """Get ETF signals for current user with DataTable support"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        user_id = session['user_id']

        # Base query for user's ETF signals
        base_query = db.session.query(ETFSignalTrade).filter(
            ETFSignalTrade.user_id == user_id
        ).options(
            joinedload(ETFSignalTrade.user),
            joinedload(ETFSignalTrade.assigned_by)
        )

        # Searchable and orderable columns
        searchable_columns = ['symbol', 'etf_name', 'trade_title', 'signal_type', 'status']
        orderable_columns = ['symbol', 'entry_price', 'current_price', 'quantity', 
                           'pnl_amount', 'pnl_percent', 'created_at', 'status']

        # Process DataTable request
        processor = DataTableProcessor(ETFSignalTrade, base_query)
        result = processor.process_request(
            request.get_json() or request.form.to_dict(),
            searchable_columns,
            orderable_columns
        )

        # Format data for DataTable
        formatted_data = []
        for trade in result['data']:
            # Get latest quote for real-time calculations
            latest_quote = RealtimeQuote.query.filter(
                RealtimeQuote.symbol == trade.symbol
            ).order_by(RealtimeQuote.timestamp.desc()).first()

            if latest_quote:
                trade.current_price = latest_quote.current_price
                trade.calculate_pnl()
                db.session.commit()

            trade_dict = trade.to_dict()

            # Add calculated fields
            investment = float(trade.invested_amount) if trade.invested_amount else 0
            current_value = float(trade.current_value) if trade.current_value else investment
            pnl_amount = float(trade.pnl_amount) if trade.pnl_amount else 0
            pnl_percent = float(trade.pnl_percent) if trade.pnl_percent else 0

            # Format for display
            trade_dict.update({
                'investment_formatted': f"₹{investment:,.2f}",
                'current_value_formatted': f"₹{current_value:,.2f}",
                'pnl_amount_formatted': f"₹{pnl_amount:,.2f}",
                'pnl_percent_formatted': f"{pnl_percent:.2f}%",
                'entry_price_formatted': f"₹{float(trade.entry_price):,.2f}" if trade.entry_price else "₹0.00",
                'current_price_formatted': f"₹{float(trade.current_price):,.2f}" if trade.current_price else "₹0.00",
                'target_price_formatted': f"₹{float(trade.target_price):,.2f}" if trade.target_price else "N/A",
                'stop_loss_formatted': f"₹{float(trade.stop_loss):,.2f}" if trade.stop_loss else "N/A",
                'status_badge': get_status_badge(trade.status),
                'signal_type_badge': get_signal_type_badge(trade.signal_type),
                'priority_badge': get_priority_badge(trade.priority),
                'last_update': latest_quote.timestamp.strftime('%H:%M:%S') if latest_quote else 'N/A'
            })

            formatted_data.append(trade_dict)

        result['data'] = formatted_data
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting user ETF signals datatable: {str(e)}")
        return jsonify({'error': str(e)}), 500

@datatable_bp.route('/etf-signals/admin', methods=['POST'])
def get_admin_etf_signals_datatable():
    """Get all ETF signals for admin with DataTable support"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        # Base query for all ETF signals with user info
        base_query = db.session.query(ETFSignalTrade).options(
            joinedload(ETFSignalTrade.user),
            joinedload(ETFSignalTrade.assigned_by)
        )

        # Searchable and orderable columns
        searchable_columns = ['symbol', 'etf_name', 'trade_title', 'signal_type', 'status']
        orderable_columns = ['symbol', 'entry_price', 'current_price', 'quantity', 
                           'pnl_amount', 'pnl_percent', 'created_at', 'user_id']

        # Process DataTable request
        processor = DataTableProcessor(ETFSignalTrade, base_query)
        result = processor.process_request(
            request.get_json() or request.form.to_dict(),
            searchable_columns,
            orderable_columns
        )

        # Format data for DataTable
        formatted_data = []
        for trade in result['data']:
            # Get latest quote for real-time calculations
            latest_quote = RealtimeQuote.query.filter(
                RealtimeQuote.symbol == trade.symbol
            ).order_by(RealtimeQuote.timestamp.desc()).first()

            if latest_quote:
                trade.current_price = latest_quote.current_price
                trade.calculate_pnl()
                db.session.commit()

            trade_dict = trade.to_dict()

            # Add user information
            user_info = {
                'user_ucc': trade.user.ucc if trade.user else 'N/A',
                'user_name': trade.user.greeting_name if trade.user else 'N/A',
                'user_mobile': trade.user.mobile_number if trade.user else 'N/A'
            }
            trade_dict.update(user_info)

            # Add calculated fields
            investment = float(trade.invested_amount) if trade.invested_amount else 0
            current_value = float(trade.current_value) if trade.current_value else investment
            pnl_amount = float(trade.pnl_amount) if trade.pnl_amount else 0
            pnl_percent = float(trade.pnl_percent) if trade.pnl_percent else 0

            # Format for display
            trade_dict.update({
                'investment_formatted': f"₹{investment:,.2f}",
                'current_value_formatted': f"₹{current_value:,.2f}",
                'pnl_amount_formatted': f"₹{pnl_amount:,.2f}",
                'pnl_percent_formatted': f"{pnl_percent:.2f}%",
                'entry_price_formatted': f"₹{float(trade.entry_price):,.2f}" if trade.entry_price else "₹0.00",
                'current_price_formatted': f"₹{float(trade.current_price):,.2f}" if trade.current_price else "₹0.00",
                'target_price_formatted': f"₹{float(trade.target_price):,.2f}" if trade.target_price else "N/A",
                'stop_loss_formatted': f"₹{float(trade.stop_loss):,.2f}" if trade.stop_loss else "N/A",
                'status_badge': get_status_badge(trade.status),
                'signal_type_badge': get_signal_type_badge(trade.signal_type),
                'priority_badge': get_priority_badge(trade.priority),
                'last_update': latest_quote.timestamp.strftime('%H:%M:%S') if latest_quote else 'N/A'
            })

            formatted_data.append(trade_dict)

        result['data'] = formatted_data
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting admin ETF signals datatable: {str(e)}")
        return jsonify({'error': str(e)}), 500

@datatable_bp.route('/admin-signals', methods=['POST'])
def get_admin_signals_datatable():
    """Get admin trade signals with DataTable support"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        # Base query for admin signals
        base_query = db.session.query(AdminTradeSignal).options(
            joinedload(AdminTradeSignal.admin_user),
            joinedload(AdminTradeSignal.target_user)
        )

        # Searchable and orderable columns
        searchable_columns = ['symbol', 'trading_symbol', 'signal_title', 'signal_type', 'status']
        orderable_columns = ['symbol', 'entry_price', 'current_price', 'quantity', 
                           'created_at', 'status', 'priority']

        # Process DataTable request
        processor = DataTableProcessor(AdminTradeSignal, base_query)
        result = processor.process_request(
            request.get_json() or request.form.to_dict(),
            searchable_columns,
            orderable_columns
        )

        # Format data for DataTable
        formatted_data = []
        for signal in result['data']:
            # Get latest quote
            latest_quote = RealtimeQuote.query.filter(
                RealtimeQuote.symbol == signal.symbol
            ).order_by(RealtimeQuote.timestamp.desc()).first()

            if latest_quote:
                signal.current_price = latest_quote.current_price
                if signal.entry_price:
                    change_pct = ((float(latest_quote.current_price) - float(signal.entry_price)) / float(signal.entry_price)) * 100
                    signal.change_percent = change_pct
                signal.last_update_time = datetime.utcnow()
                db.session.commit()

            # Calculate values
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            current_price = float(signal.current_price) if signal.current_price else entry_price
            target_price = float(signal.target_price) if signal.target_price else 0
            quantity = signal.quantity or 0
            pnl = (current_price - entry_price) * quantity
            pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

            # Calculate additional fields
            investment = float(signal.entry_price * signal.quantity) if signal.entry_price else 0
            current_value = float(signal.current_price * signal.quantity) if signal.current_price else 0
            target_value = float(signal.target_price * signal.quantity) if signal.target_price else 0

            # Format data exactly as requested with field names
            trade_dict = {
                'user_target_id': signal.target_user_id,
                'Symbol': signal.symbol,
                '30': '-',
                'DH': f"₹{float(latest_quote.high_price):,.2f}" if latest_quote and latest_quote.high_price else '-',
                'Date': signal.created_at.strftime('%Y-%m-%d') if signal.created_at else '',
                'Pos': signal.signal_type,
                'Qty': signal.quantity,
                'EP': f"₹{float(signal.entry_price):,.2f}" if signal.entry_price else '-',
                'CMP': f"₹{float(signal.current_price):,.2f}" if signal.current_price else '-',
                '%Chan': f"{pnl_percent:+.2f}%" if pnl_percent else '0.00%',
                'Inv.': f"₹{investment:,.2f}",
                'TP': f"₹{float(signal.target_price):,.2f}" if signal.target_price else '-',
                'TVA': f"₹{target_value:,.2f}" if target_value else '-',
                'TPR': f"{((float(signal.target_price) - float(signal.entry_price)) / float(signal.entry_price) * 100):+.2f}%" if signal.target_price and signal.entry_price else '-',
                'PL': f"₹{pnl:+,.2f}",
                'ED': signal.updated_at.strftime('%Y-%m-%d') if signal.status != 'ACTIVE' else '-',
                'PR': f"{(pnl / investment * 100):+.2f}%" if investment > 0 else '-',
                'PP': f"{pnl_percent:+.1f}" if pnl_percent else '0.0',
                'IV': f"₹{investment:,.2f}",
                'IP': '100.00%',
                'NT': f"₹{current_value:,.2f}",
                'Qt': f"₹{float(signal.current_price):,.2f}" if signal.current_price else '-',
                '7': '-',
                '%Ch': f"{pnl_percent:+.2f}%" if pnl_percent else '0.00%'
            }

            formatted_data.append(trade_dict)

        result['data'] = formatted_data
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting admin signals datatable: {str(e)}")
        return jsonify({'error': str(e)}), 500

@datatable_bp.route('/realtime-quotes', methods=['POST'])
def get_realtime_quotes_datatable():
    """Get realtime quotes with DataTable support"""
    try:
        # Get latest quotes only (one per symbol)
        subquery = db.session.query(
            RealtimeQuote.symbol,
            db.func.max(RealtimeQuote.timestamp).label('max_timestamp')
        ).group_by(RealtimeQuote.symbol).subquery()

        base_query = db.session.query(RealtimeQuote).join(
            subquery,
            and_(
                RealtimeQuote.symbol == subquery.c.symbol,
                RealtimeQuote.timestamp == subquery.c.max_timestamp
            )
        )

        # Searchable and orderable columns
        searchable_columns = ['symbol', 'trading_symbol', 'exchange']
        orderable_columns = ['symbol', 'current_price', 'change_percent', 'volume', 'timestamp']

        # Process DataTable request
        processor = DataTableProcessor(RealtimeQuote, base_query)
        result = processor.process_request(
            request.get_json() or request.form.to_dict(),
            searchable_columns,
            orderable_columns
        )

        # Format data for DataTable
        formatted_data = []
        for quote in result['data']:
            quote_dict = quote.to_dict()

            # Format for display
            quote_dict.update({
                'current_price_formatted': f"₹{float(quote.current_price):,.2f}",
                'change_amount_formatted': f"₹{float(quote.change_amount):,.2f}" if quote.change_amount else "₹0.00",
                'change_percent_formatted': f"{float(quote.change_percent):,.2f}%" if quote.change_percent else "0.00%",
                'volume_formatted': f"{quote.volume:,}" if quote.volume else "0",
                'timestamp_formatted': quote.timestamp.strftime('%H:%M:%S'),
                'status_badge': get_market_status_badge(quote.market_status)
            })

            formatted_data.append(quote_dict)

        result['data'] = formatted_data
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting realtime quotes datatable: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_status_badge(status):
    """Get HTML badge for status"""
    status_colors = {
        'ACTIVE': 'success',
        'CLOSED': 'secondary',
        'CANCELLED': 'danger',
        'EXPIRED': 'warning',
        'EXECUTED': 'info'
    }
    color = status_colors.get(status, 'primary')
    return f'<span class="badge bg-{color}">{status}</span>'

def get_signal_type_badge(signal_type):
    """Get HTML badge for signal type"""
    type_colors = {
        'BUY': 'success',
        'SELL': 'danger',
        'HOLD': 'warning'
    }
    color = type_colors.get(signal_type, 'primary')
    return f'<span class="badge bg-{color}">{signal_type}</span>'

def get_priority_badge(priority):
    """Get HTML badge for priority"""
    priority_colors = {
        'HIGH': 'danger',
        'MEDIUM': 'warning',
        'LOW': 'info'
    }
    color = priority_colors.get(priority, 'secondary')
    return f'<span class="badge bg-{color}">{priority}</span>'

def get_market_status_badge(status):
    """Get HTML badge for market status"""
    status_colors = {
        'OPEN': 'success',
        'CLOSED': 'danger',
        'PRE_OPEN': 'warning'
    }
    color = status_colors.get(status, 'secondary')
    return f'<span class="badge bg-{color}">{status}</span>'