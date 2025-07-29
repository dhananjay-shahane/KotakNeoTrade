"""
Candlestick Charts API
Provides endpoints for candlestick chart data using external PostgreSQL database
"""

from flask import Blueprint, jsonify, request
import logging
import datetime
from dateutil.relativedelta import relativedelta
from Scripts.external_db_service import create_db_connection

logger = logging.getLogger(__name__)

candlestick_bp = Blueprint('candlestick_api', __name__)


def table_exists(db_connector, table_name):
    """Check if a table exists in the symbols schema"""
    try:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'symbols' 
                AND table_name = %s
            )
        """
        result = db_connector.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False
    except:
        return False


def get_cmp(db_connector, symbol):
    """Get current market price from 5m table (from most recent trading day)"""
    table_name = f"{symbol.lower()}_5m"
    if not table_exists(db_connector, table_name):
        logger.warning(f"Table not found: symbols.{table_name}")
        return None

    try:
        query = f"""
            SELECT close 
            FROM symbols.{table_name}
            WHERE EXTRACT(DOW FROM datetime) BETWEEN 1 AND 5
            ORDER BY datetime DESC 
            LIMIT 1
        """
        result = db_connector.execute_query(query)
        return float(result[0]['close']) if result else None
    except Exception as e:
        logger.error(f"Error fetching CMP: {e}")
        return None


def get_historical_cmp(db_connector, symbol, offset):
    """Get historical close price N trading days ago (excluding weekends)"""
    table_name = f"{symbol.lower()}_daily"
    if not table_exists(db_connector, table_name):
        return None

    try:
        query = f"""
            SELECT close
            FROM (
                SELECT datetime, close,
                       ROW_NUMBER() OVER (ORDER BY datetime DESC) as rn
                FROM symbols.{table_name}
                WHERE EXTRACT(DOW FROM datetime) BETWEEN 1 AND 5
            ) t
            WHERE rn = {offset + 1}
        """
        result = db_connector.execute_query(query)
        return float(result[0]['close']) if result else None
    except Exception as e:
        logger.error(f"Error fetching historical CMP: {e}")
        return None


def get_ohlc_data(db_connector, symbol, period='1M'):
    """Get OHLC data for candlestick chart with aggressive optimization for performance"""
    daily_table = f"{symbol.lower()}_daily"
    intraday_table = f"{symbol.lower()}_5m"

    try:
        # Handle different time periods with strict limits for performance
        today = datetime.date.today()

        if period == '1D':
            # Intraday data for current trading day only with IST time
            if not table_exists(db_connector, intraday_table):
                return []

            # Get the most recent trading day (excluding weekends)
            query = f"""
                WITH latest_trading_day AS (
                    SELECT MAX(datetime::date) as trading_date
                    FROM symbols.{intraday_table}
                    WHERE datetime::date <= CURRENT_DATE
                    AND EXTRACT(DOW FROM datetime) NOT IN (0, 6)
                    AND datetime >= CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT 
                    datetime AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as datetime,
                    open, high, low, close, volume
                FROM symbols.{intraday_table}, latest_trading_day
                WHERE datetime::date = latest_trading_day.trading_date
                AND EXTRACT(DOW FROM datetime) NOT IN (0, 6)
                ORDER BY datetime ASC
                LIMIT 200
            """
            result = db_connector.execute_query(query)
            return result if result else []

        else:
            # Daily data with aggressive limits for speed
            if not table_exists(db_connector, daily_table):
                return []

            # Strict limits for faster loading
            if period == '1W':
                limit_rows = 5
            elif period == '1M':
                limit_rows = 20  # Reduced from 30
            elif period == '3M':
                limit_rows = 65  # Reduced from 90
            elif period == '6M':
                limit_rows = 120  # Reduced from 180
            elif period == 'YTD':
                limit_rows = min(200, (today -
                                       datetime.date(today.year, 1, 1)).days)
            elif period == '1Y':
                limit_rows = 200  # Reduced from 365
            elif period == '5Y':
                limit_rows = 500  # Reduced from 1250
            else:  # MAX
                limit_rows = 1000  # Reduced from 2500

            # Ultra-optimized query - get latest N trading days, strictly exclude weekends
            query = f"""
                SELECT datetime, open, high, low, close, volume
                FROM (
                    SELECT datetime, open, high, low, close, volume
                    FROM symbols.{daily_table}
                    WHERE EXTRACT(DOW FROM datetime) BETWEEN 1 AND 5
                    AND datetime <= (
                        SELECT MAX(datetime) 
                        FROM symbols.{daily_table} 
                        WHERE EXTRACT(DOW FROM datetime) BETWEEN 1 AND 5
                    )
                    ORDER BY datetime DESC
                    LIMIT {limit_rows}
                ) t
                ORDER BY datetime ASC
            """

            result = db_connector.execute_query(query)
            return result if result else []

    except Exception as e:
        logger.error(f"Error fetching OHLC data: {e}")
        return []


@candlestick_bp.route('/candlestick-data')
def get_candlestick_data():
    """Get candlestick chart data for a symbol with aggressive performance optimization"""
    try:
        symbol = request.args.get('symbol', '').strip().upper()
        period = request.args.get('period', '1M')

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Validate period to prevent excessive queries
        valid_periods = [
            '1D', '1W', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'MAX'
        ]
        if period not in valid_periods:
            return jsonify({'error': 'Invalid period specified'}), 400

        # Create connection with error handling
        try:
            db_connector = create_db_connection()
            if not db_connector:
                return jsonify({'error': 'Database connection failed'}), 500
        except Exception as conn_error:
            logger.error(f"Database connection error: {conn_error}")
            return jsonify({'error': 'Database service unavailable'}), 503

        try:
            # Get OHLC data with optimized query
            ohlc_data = get_ohlc_data(db_connector, symbol, period)

            if not ohlc_data:
                return jsonify({
                    'error':
                    f'No data available for {symbol} in {period} period',
                    'symbol': symbol,
                    'period': period,
                    'data': []
                })

            # Fast data formatting with minimal processing
            formatted_data = []
            for row in ohlc_data:
                try:
                    # Direct conversion without extra checks for speed
                    formatted_data.append({
                        'x':
                        str(row['datetime']),
                        'open':
                        float(row['open']),
                        'high':
                        float(row['high']),
                        'low':
                        float(row['low']),
                        'close':
                        float(row['close']),
                        'volume':
                        int(row.get('volume', 0) or 0)
                    })
                except (ValueError, TypeError, KeyError):
                    # Skip invalid rows silently for speed
                    continue

            if not formatted_data:
                return jsonify({
                    'error': f'No valid data found for {symbol}',
                    'symbol': symbol,
                    'period': period,
                    'data': []
                })

            # Add cache headers for client-side caching
            response = jsonify({
                'success': True,
                'symbol': symbol,
                'period': period,
                'data': formatted_data,
                'count': len(formatted_data)
            })
            response.headers[
                'Cache-Control'] = 'public, max-age=60'  # 1 minute cache
            return response

        except Exception as query_error:
            logger.error(f"Query error for {symbol} {period}: {query_error}")
            return jsonify({
                'error':
                'Database query timeout. Try a shorter time period.'
            }), 408

        finally:
            if db_connector:
                try:
                    if hasattr(db_connector, 'close'):
                        db_connector.close()
                except:
                    pass

    except Exception as e:
        symbol_name = locals().get('symbol', 'unknown')
        period_name = locals().get('period', 'unknown')
        logger.error(
            f"Error in candlestick data API for {symbol_name} {period_name}: {e}")
        return jsonify({'error': f'Service temporarily unavailable'}), 503


@candlestick_bp.route('/symbol-metrics')
def get_symbol_metrics():
    """Get symbol metrics (current price, changes)"""
    try:
        symbol = request.args.get('symbol', '').strip().upper()

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        db_connector = create_db_connection()
        if not db_connector:
            return jsonify({'error': 'Database connection failed'}), 500

        try:
            # Get current and historical prices
            cmp = get_cmp(db_connector, symbol)
            cmp_5d = get_historical_cmp(db_connector, symbol, 5)
            cmp_1m = get_historical_cmp(db_connector, symbol, 20)

            # Calculate percentage changes
            def calc_pct(current, historical):
                if None in (current, historical) or historical == 0:
                    return None, '--'
                pct = ((current - historical) / historical) * 100
                return pct, f"{pct:+.2f}%"

            pct_5d_val, pct_5d_str = calc_pct(cmp, cmp_5d)
            pct_1m_val, pct_1m_str = calc_pct(cmp, cmp_1m)

            metrics = {
                'symbol': symbol,
                'current_price': cmp,
                'price_5d_ago': cmp_5d,
                'price_1m_ago': cmp_1m,
                'change_5d_pct': pct_5d_val,
                'change_5d_str': pct_5d_str,
                'change_1m_pct': pct_1m_val,
                'change_1m_str': pct_1m_str
            }

            return jsonify({'success': True, 'metrics': metrics})

        finally:
            if db_connector:
                try:
                    if hasattr(db_connector, 'close'):
                        db_connector.close()
                except:
                    pass

    except Exception as e:
        logger.error(f"Error in symbol metrics API: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@candlestick_bp.route('/available-symbols')
def get_available_symbols():
    """Get list of available symbols for charting with search support"""
    try:
        search_query = request.args.get('search', '').strip().upper()
        categories = request.args.get('categories', 'NIFTY').split(',')

        db_connector = create_db_connection()
        if not db_connector:
            return jsonify({'error': 'Database connection failed'}), 500

        try:
            # Get all symbols ending with _daily from symbols schema
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'symbols' 
                AND table_name LIKE '%_daily'
                ORDER BY table_name
            """

            result = db_connector.execute_query(query)
            if not result:
                return jsonify({'success': True, 'symbols': [], 'count': 0})

            # Extract symbol names (remove _daily suffix and convert to uppercase)
            all_symbols = []
            if result and hasattr(result, '__iter__'):
                for row in result:
                    table_name = row['table_name']
                    if table_name.endswith('_daily'):
                        symbol = table_name[:-6].upper()  # Remove '_daily' suffix
                        all_symbols.append(symbol)

            # Filter by categories (basic filtering - you can enhance this)
            category_filtered_symbols = []
            for symbol in all_symbols:
                if 'NIFTY' in categories and ('NIFTY' in symbol or symbol in [
                        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
                        'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT'
                ]):
                    category_filtered_symbols.append(symbol)
                elif 'NIFTY500' in categories and symbol not in category_filtered_symbols:
                    category_filtered_symbols.append(symbol)
                elif 'ETF' in categories and 'ETF' in symbol:
                    category_filtered_symbols.append(symbol)

            # Remove duplicates while preserving order
            category_filtered_symbols = list(
                dict.fromkeys(category_filtered_symbols))

            # Filter symbols based on search query if provided
            if search_query:
                filtered_symbols = [
                    symbol for symbol in category_filtered_symbols
                    if search_query in symbol
                ]
            else:
                filtered_symbols = category_filtered_symbols

            return jsonify({
                'success': True,
                'symbols': filtered_symbols[:50],  # Limit to 50 results
                'count': len(filtered_symbols)
            })

        finally:
            if db_connector:
                try:
                    if hasattr(db_connector, 'close'):
                        db_connector.close()
                except:
                    pass

    except Exception as e:
        logger.error(f"Error in available symbols API: {e}")
        return jsonify({'error': 'Internal server error'}), 500
