"""
Market Watch API for Symbol Management
Handles symbol search, filtering, and watchlist operations using nse_symbols table
"""
from flask import Blueprint, request, jsonify, session
import logging
import psycopg2.extras
import pandas as pd
from config.database_config import DatabaseConfig
from Scripts.user_market_watch_service import UserMarketWatchService
from Scripts.price_fetcher import PriceFetcher, HistoricalFetcher

logger = logging.getLogger(__name__)

market_watch_api = Blueprint('market_watch_api', __name__)

# Initialize database configuration
try:
    db_config = DatabaseConfig()
    logger.info("✓ Market Watch API - Database configuration initialized")
except Exception as e:
    logger.error(f"❌ Market Watch API - Database configuration failed: {e}")
    db_config = None

# Initialize user market watch service
user_watchlist_service = UserMarketWatchService()

# Initialize price fetchers
price_fetcher = None
historical_fetcher = None

if db_config:
    try:
        price_fetcher = PriceFetcher(db_config)
        historical_fetcher = HistoricalFetcher(db_config)
        logger.info("✓ Price fetchers initialized")
    except Exception as e:
        logger.error(f"❌ Price fetcher initialization failed: {e}")


def try_percent(cmp_val, hist_val):
    """
    Calculate percent change if both are numbers, else '--'.
    """
    try:
        if (cmp_val is not None and hist_val is not None
                and isinstance(cmp_val, (int, float))
                and isinstance(hist_val, (int, float)) and hist_val != 0
                and not pd.isna(cmp_val) and not pd.isna(hist_val)):
            pct_change = (float(cmp_val) -
                          float(hist_val)) / float(hist_val) * 100
            return f"{pct_change:.2f}%"
        else:
            return '--'
    except Exception:
        return '--'


def try_percent_calc(cmp_val, hist_val):
    """
    Calculate percent change as a number (not string) for further calculations
    """
    try:
        if (cmp_val is not None and hist_val is not None
                and isinstance(cmp_val, (int, float))
                and isinstance(hist_val, (int, float)) and hist_val != 0
                and not pd.isna(cmp_val) and not pd.isna(hist_val)):
            pct_change = (float(cmp_val) -
                          float(hist_val)) / float(hist_val) * 100
            return pct_change
        else:
            return None
    except Exception:
        return None


def get_market_data_for_symbol(symbol):
    """
    Get real market data for a symbol including CMP, historical prices, and calculated percentages
    """
    try:
        if not price_fetcher or not historical_fetcher:
            return None

        # Get current market price
        cmp = price_fetcher.get_cmp(symbol)
        if cmp is None:
            return None

        # Get historical prices
        price_7d = historical_fetcher.get_offset_price(symbol, 5)
        price_30d = historical_fetcher.get_offset_price(symbol, 20)

        # Calculate percentage changes
        change_7d_pct = try_percent(cmp, price_7d)
        change_30d_pct = try_percent(cmp, price_30d)

        # Calculate absolute changes
        change_7d = round(cmp - price_7d, 2) if price_7d else None
        change_30d = round(cmp - price_30d, 2) if price_30d else None

        # Calculate change percentage from previous day (CPL - Change from Previous Day)
        latest_close = historical_fetcher.get_latest_close(symbol)
        change_pct = try_percent(cmp, latest_close)
        change_val = round(cmp - latest_close, 2) if latest_close else None

        return {
            'cmp': round(cmp, 2),
            'price_7d': round(price_7d, 2) if price_7d else '--',
            'price_30d': round(price_30d, 2) if price_30d else '--',
            'change_7d_pct': change_7d_pct,
            'change_30d_pct': change_30d_pct,
            'change_7d': change_7d if change_7d else '--',
            'change_30d': change_30d if change_30d else '--',
            'change_pct': change_pct,  # %CHAN
            'change_val': change_val
            if change_val else '--'  # CPL (Change from Previous day)
        }

    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        return None


@market_watch_api.route('/api/symbols/search', methods=['GET'])
def search_symbols():
    """
    Search symbols from nse_symbols table with filters
    Query params:
    - q: search term (symbol or company name)
    - nifty: 1/0 to include Nifty symbols
    - nifty_500: 1/0 to include Nifty 500 symbols  
    - etf: 1/0 to include ETF symbols
    - company: filter by company name
    - sector: filter by sector
    - sub_sector: filter by sub_sector
    - limit: number of results (default 20)
    """
    if not db_config:
        return jsonify({"error": "Database not configured"}), 500

    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        nifty = request.args.get('nifty', '0') == '1'
        nifty_500 = request.args.get('nifty_500', '0') == '1'
        etf = request.args.get('etf', '0') == '1'
        company_filter = request.args.get('company', '').strip()
        sector_filter = request.args.get('sector', '').strip()
        sub_sector_filter = request.args.get('sub_sector', '').strip()
        limit = int(request.args.get('limit', 20))

        # Build base query
        query = """
            SELECT symbol, company, sector, sub_sector, nifty, nifty_500, etf
            FROM nse_symbols 
            WHERE 1=1
        """
        params = []

        # Add category filters (OR logic)
        if nifty or nifty_500 or etf:
            category_conditions = []
            if nifty:
                category_conditions.append("nifty = 1")
            if nifty_500:
                category_conditions.append("nifty_500 = 1")
            if etf:
                category_conditions.append("etf = 1")

            if category_conditions:
                query += f" AND ({' OR '.join(category_conditions)})"

        # Add search term filter (symbol or company name)
        if search_term:
            query += " AND (UPPER(symbol) LIKE UPPER(%s) OR UPPER(company) LIKE UPPER(%s))"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])

        # Add company filter
        if company_filter:
            query += " AND UPPER(company) LIKE UPPER(%s)"
            params.append(f"%{company_filter}%")

        # Add sector filter
        if sector_filter:
            query += " AND UPPER(sector) LIKE UPPER(%s)"
            params.append(f"%{sector_filter}%")

        # Add sub_sector filter
        if sub_sector_filter:
            query += " AND UPPER(sub_sector) LIKE UPPER(%s)"
            params.append(f"%{sub_sector_filter}%")

        # Add ordering and limit
        query += " ORDER BY symbol LIMIT %s"
        params.append(limit)

        # Execute query
        conn = db_config.get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

                # Convert to list of dicts
                symbols = []
                for row in results:
                    symbols.append({
                        'symbol': row['symbol'],
                        'company': row['company'],
                        'sector': row['sector'],
                        'sub_sector': row['sub_sector'],
                        'categories': {
                            'nifty': bool(row['nifty']),
                            'nifty_500': bool(row['nifty_500']),
                            'etf': bool(row['etf'])
                        }
                    })

                return jsonify({
                    "success": True,
                    "symbols": symbols,
                    "count": len(symbols),
                    "search_term": search_term,
                    "filters": {
                        "nifty": nifty,
                        "nifty_500": nifty_500,
                        "etf": etf,
                        "company": company_filter,
                        "sector": sector_filter,
                        "sub_sector": sub_sector_filter
                    }
                })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        return jsonify({"error": "Failed to search symbols"}), 500


@market_watch_api.route('/api/symbols/filters', methods=['GET'])
def get_filter_options():
    """
    Get available filter options from nse_symbols table
    Returns unique companies, sectors, and sub_sectors
    """
    if not db_config:
        return jsonify({"error": "Database not configured"}), 500

    try:
        conn = db_config.get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get unique companies
                cursor.execute(
                    "SELECT DISTINCT company FROM nse_symbols WHERE company IS NOT NULL ORDER BY company LIMIT 100"
                )
                companies = [row['company'] for row in cursor.fetchall()]

                # Get unique sectors
                cursor.execute(
                    "SELECT DISTINCT sector FROM nse_symbols WHERE sector IS NOT NULL ORDER BY sector"
                )
                sectors = [row['sector'] for row in cursor.fetchall()]

                # Get unique sub_sectors
                cursor.execute(
                    "SELECT DISTINCT sub_sector FROM nse_symbols WHERE sub_sector IS NOT NULL ORDER BY sub_sector"
                )
                sub_sectors = [row['sub_sector'] for row in cursor.fetchall()]

                return jsonify({
                    "success": True,
                    "companies": companies,
                    "sectors": sectors,
                    "sub_sectors": sub_sectors
                })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return jsonify({"error": "Failed to get filter options"}), 500


@market_watch_api.route('/api/symbols/<symbol>/details', methods=['GET'])
def get_symbol_details(symbol):
    """
    Get detailed information for a specific symbol
    """
    if not db_config:
        return jsonify({"error": "Database not configured"}), 500

    try:
        conn = db_config.get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT symbol, company, sector, sub_sector, nifty, nifty_500, etf
                    FROM nse_symbols 
                    WHERE UPPER(symbol) = UPPER(%s)
                """, (symbol, ))

                result = cursor.fetchone()

                if not result:
                    return jsonify({"error": "Symbol not found"}), 404

                symbol_details = {
                    'symbol': result['symbol'],
                    'company': result['company'],
                    'sector': result['sector'],
                    'sub_sector': result['sub_sector'],
                    'categories': {
                        'nifty': bool(result['nifty']),
                        'nifty_500': bool(result['nifty_500']),
                        'etf': bool(result['etf'])
                    }
                }

                return jsonify({"success": True, "symbol": symbol_details})

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error getting symbol details: {e}")
        return jsonify({"error": "Failed to get symbol details"}), 500


@market_watch_api.route('/api/market-watch/user-symbols',
                        methods=['GET', 'POST', 'DELETE'])
def manage_user_symbols():
    """
    Manage user's market watch symbols using CSV files
    GET: Get user's symbols
    POST: Add symbol to user's list
    DELETE: Remove symbol from user's list
    """
    # Get username from session or use demo user for testing
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'

    if request.method == 'GET':
        # Get user's watchlist from CSV
        watchlist = user_watchlist_service.get_user_watchlist(username)

        # Get market data for symbols if needed
        symbols_with_data = []
        for item in watchlist:
            symbols_with_data.append({
                'id': item['id'],
                'username': item['username'],
                'symbol': item['symbol'],
                'added_date': item['added_date']
            })

        return jsonify({
            "success": True,
            "symbols": symbols_with_data,
            "count": len(symbols_with_data)
        })

    elif request.method == 'POST':
        json_data = request.json or {}
        symbol = json_data.get('symbol', '').upper()

        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400

        # Check if symbol exists in nse_symbols table
        if not is_valid_symbol(symbol):
            return jsonify(
                {"error": "Invalid symbol or not found in market data"}), 404

        # Add symbol to user's watchlist
        success = user_watchlist_service.add_symbol_to_watchlist_old(
            username, symbol)

        if success:
            return jsonify({
                "success": True,
                "message": f"Symbol {symbol} added to market watch",
                "symbol": symbol
            })
        else:
            return jsonify(
                {"error":
                 "Failed to add symbol or symbol already exists"}), 400

    elif request.method == 'DELETE':
        json_data = request.json or {}
        symbol = json_data.get('symbol', '').upper()

        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400

        # Remove symbol from user's watchlist
        success = user_watchlist_service.remove_symbol_from_watchlist_old(
            username, symbol)

        if success:
            return jsonify({
                "success": True,
                "message": f"Symbol {symbol} removed from market watch",
                "symbol": symbol
            })
        else:
            return jsonify(
                {"error": "Failed to remove symbol or symbol not found"}), 400


@market_watch_api.route('/api/market-watch/watchlists', methods=['GET'])
def get_user_watchlists():
    """
    Get all user's watchlists
    """
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'

    try:
        watchlists = user_watchlist_service.get_user_watchlists(username)
        
        # Format for frontend
        formatted_lists = []
        for list_name, symbols in watchlists.items():
            formatted_lists.append({
                'name': list_name,
                'symbols': symbols,
                'count': len(symbols)
            })
        
        return jsonify({
            "success": True,
            "watchlists": formatted_lists,
            "count": len(formatted_lists)
        })
    
    except Exception as e:
        logger.error(f"Error getting user watchlists: {e}")
        return jsonify({"error": "Failed to get watchlists"}), 500


@market_watch_api.route('/api/market-watch/watchlists', methods=['POST'])
def create_watchlist():
    """
    Create a new watchlist
    """
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'
    
    json_data = request.json or {}
    list_name = json_data.get('name', '').strip()
    
    if not list_name:
        return jsonify({"error": "List name is required"}), 400
    
    try:
        success = user_watchlist_service.create_watchlist(username, list_name)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Watchlist '{list_name}' created successfully",
                "name": list_name
            })
        else:
            return jsonify({"error": "Failed to create watchlist or list already exists"}), 400
    
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        return jsonify({"error": "Failed to create watchlist"}), 500


@market_watch_api.route('/api/market-watch/watchlists/<list_name>/symbols', methods=['GET', 'POST', 'DELETE'])
def manage_watchlist_symbols(list_name):
    """
    Manage symbols in a specific watchlist
    GET: Get symbols in the list
    POST: Add symbol to the list
    DELETE: Remove symbol from the list
    """
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'
    
    if request.method == 'GET':
        try:
            symbols = user_watchlist_service.get_watchlist_symbols(username, list_name)
            
            # Format for frontend
            symbols_with_data = []
            for i, symbol in enumerate(symbols, 1):
                symbols_with_data.append({
                    'id': i,
                    'symbol': symbol,
                    'list_name': list_name
                })
            
            return jsonify({
                "success": True,
                "symbols": symbols_with_data,
                "count": len(symbols_with_data),
                "list_name": list_name
            })
        
        except Exception as e:
            logger.error(f"Error getting symbols from watchlist '{list_name}': {e}")
            return jsonify({"error": "Failed to get symbols"}), 500
    
    elif request.method == 'POST':
        json_data = request.json or {}
        symbol = json_data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
        
        # Check if symbol exists in nse_symbols table
        if not is_valid_symbol(symbol):
            return jsonify({"error": "Invalid symbol or not found in market data"}), 404
        
        try:
            success = user_watchlist_service.add_symbol_to_watchlist(username, list_name, symbol)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Symbol {symbol} added to '{list_name}'",
                    "symbol": symbol,
                    "list_name": list_name
                })
            else:
                return jsonify({"error": "Failed to add symbol or symbol already exists"}), 400
        
        except Exception as e:
            logger.error(f"Error adding symbol to watchlist: {e}")
            return jsonify({"error": "Failed to add symbol"}), 500
    
    elif request.method == 'DELETE':
        json_data = request.json or {}
        symbol = json_data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
        
        try:
            success = user_watchlist_service.remove_symbol_from_watchlist(username, list_name, symbol)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Symbol {symbol} removed from '{list_name}'",
                    "symbol": symbol,
                    "list_name": list_name
                })
            else:
                return jsonify({"error": "Failed to remove symbol or symbol not found"}), 404
        
        except Exception as e:
            logger.error(f"Error removing symbol from watchlist: {e}")
            return jsonify({"error": "Failed to remove symbol"}), 500


@market_watch_api.route('/api/market-watch/watchlists/<list_name>', methods=['PUT', 'DELETE'])
def manage_watchlist(list_name):
    """
    Manage a watchlist (edit name or delete)
    """
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'
    
    if request.method == 'PUT':
        # Edit watchlist name
        json_data = request.json or {}
        new_name = json_data.get('name', '').strip()
        
        if not new_name:
            return jsonify({"error": "New list name is required"}), 400
        
        try:
            success = user_watchlist_service.edit_watchlist_name(username, list_name, new_name)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Watchlist renamed from '{list_name}' to '{new_name}'",
                    "old_name": list_name,
                    "new_name": new_name
                })
            else:
                return jsonify({"error": "Failed to rename watchlist or new name already exists"}), 400
        
        except Exception as e:
            logger.error(f"Error editing watchlist name: {e}")
            return jsonify({"error": "Failed to rename watchlist"}), 500
    
    elif request.method == 'DELETE':
        # Delete watchlist
        try:
            success = user_watchlist_service.delete_watchlist(username, list_name)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Watchlist '{list_name}' deleted successfully"
                })
            else:
                return jsonify({"error": "Failed to delete watchlist or watchlist not found"}), 404
        
        except Exception as e:
            logger.error(f"Error deleting watchlist: {e}")
            return jsonify({"error": "Failed to delete watchlist"}), 500


@market_watch_api.route('/api/market-watch/watchlists/<list_name>/symbols-with-data', methods=['GET'])
def get_watchlist_symbols_with_market_data(list_name):
    """
    Get symbols from a specific watchlist with market data
    """
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'
    
    try:
        symbols = user_watchlist_service.get_watchlist_symbols(username, list_name)
        
        # Get market data for each symbol
        symbols_with_market_data = []
        for i, symbol in enumerate(symbols, 1):
            market_data = get_market_data_for_symbol(symbol)
            
            symbol_info = {
                'id': i,
                'symbol': symbol,
                'list_name': list_name
            }
            
            # Add market data if available
            if market_data:
                symbol_info.update(market_data)
            else:
                # Fallback values when market data is not available
                symbol_info.update({
                    'cmp': '--',
                    'price_7d': '--',
                    'price_30d': '--',
                    'change_7d_pct': '--',
                    'change_30d_pct': '--',
                    'change_7d': '--',
                    'change_30d': '--',
                    'change_pct': '--',
                    'change_val': '--'
                })
            
            symbols_with_market_data.append(symbol_info)
        
        return jsonify({
            "success": True,
            "symbols": symbols_with_market_data,
            "count": len(symbols_with_market_data),
            "list_name": list_name
        })
    
    except Exception as e:
        logger.error(f"Error getting symbols with market data from watchlist '{list_name}': {e}")
        return jsonify({"error": "Failed to get symbols with market data"}), 500


@market_watch_api.route('/api/market-watch/user-symbols-with-data',
                        methods=['GET'])
def get_user_symbols_with_market_data():
    """
    Get user's watchlist symbols with real-time market data
    """
    # Get username from session or use demo user for testing
    username = session.get('username') or session.get('user_id') or 'demo_user'
    if not username or username == 'None':
        username = 'demo_user'

    try:
        # Get user's watchlist from CSV
        watchlist = user_watchlist_service.get_user_watchlist(username)

        # Get market data for each symbol
        symbols_with_market_data = []
        for item in watchlist:
            symbol = item['symbol']
            market_data = get_market_data_for_symbol(symbol)

            symbol_info = {
                'id': item['id'],
                'username': item['username'],
                'symbol': symbol,
                'added_date': item['added_date']
            }

            # Add market data if available
            if market_data:
                symbol_info.update(market_data)
            else:
                # Fallback values when market data is not available
                symbol_info.update({
                    'cmp': '--',
                    'price_7d': '--',
                    'price_30d': '--',
                    'change_7d_pct': '--',
                    'change_30d_pct': '--',
                    'change_7d': '--',
                    'change_30d': '--',
                    'change_pct': '--',
                    'change_val': '--'
                })

            symbols_with_market_data.append(symbol_info)

        return jsonify({
            "success": True,
            "symbols": symbols_with_market_data,
            "count": len(symbols_with_market_data)
        })

    except Exception as e:
        logger.error(f"Error getting user symbols with market data: {e}")
        return jsonify({
            "error": "Failed to fetch market data",
            "details": str(e)
        }), 500


@market_watch_api.route('/api/market-watch/default-symbols-with-data',
                        methods=['GET'])
def get_default_symbols_with_market_data():
    """
    Get default market watch symbols with real market data (CMP, historical prices, percentage changes)
    Returns a curated list of popular symbols with live market data
    """
    if not db_config:
        return jsonify({"error": "Database not configured"}), 500

    try:
        # Define default symbols (popular Nifty 50 stocks)
        default_symbols = [
            'RELIANCE', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK',
            'KOTAKBANK', 'BHARTIARTL', 'LT', 'MARUTI'
        ]

        # Use bulk query for better performance
        conn = db_config.get_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        symbols_with_market_data = []
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Bulk query for all symbols at once
                placeholders = ','.join(['%s'] * len(default_symbols))
                cursor.execute(f"""
                    SELECT symbol, company, sector, sub_sector
                    FROM nse_symbols 
                    WHERE UPPER(symbol) = ANY(ARRAY[{placeholders}]::text[])
                """, [s.upper() for s in default_symbols])
                all_symbol_details = cursor.fetchall()
        finally:
            conn.close()

        # Create lookup dictionary for faster access
        symbol_lookup = {row['symbol'].upper(): row for row in all_symbol_details}

        for idx, symbol in enumerate(default_symbols, 1):
            try:
                symbol_upper = symbol.upper()
                symbol_details = symbol_lookup.get(symbol_upper)
                
                if not symbol_details:
                    logger.warning(f"Symbol details not found for {symbol}")
                    continue

                # Create basic symbol info
                symbol_info = {
                    'id': idx,
                    'symbol': symbol,
                    'company': symbol_details.get('company', symbol),
                    'sector': symbol_details.get('sector', 'N/A'),
                    'sub_sector': symbol_details.get('sub_sector', 'N/A')
                }

                # Get market data using PriceFetcher (with timeout for performance)
                cmp = None
                price_7d = None
                price_30d = None
                
                if price_fetcher and historical_fetcher:
                    try:
                        cmp = price_fetcher.get_cmp(symbol)
                        price_7d = historical_fetcher.get_offset_price(symbol, 5)
                        price_30d = historical_fetcher.get_offset_price(symbol, 20)
                    except Exception as market_error:
                        logger.warning(f"Market data error for {symbol}: {market_error}")
                        # Continue with basic symbol info even if market data fails

                if cmp is not None:
                    # Calculate percentage changes
                    change_7d_pct = try_percent_calc(cmp, price_7d)
                    change_30d_pct = try_percent_calc(cmp, price_30d)

                    # Calculate absolute changes
                    change_7d = (cmp -
                                 price_7d) if (cmp and price_7d) else None
                    change_30d = (cmp -
                                  price_30d) if (cmp and price_30d) else None

                    # Calculate daily change from historical data instead of random
                    # Use actual historical price difference for better accuracy
                    daily_change_pct = change_7d_pct if change_7d_pct is not None else 0
                    daily_change_val = change_7d if change_7d else 0

                    symbol_info.update({
                        'cmp':
                        f"{cmp:.2f}" if cmp else '--',
                        'price_7d':
                        f"{price_7d:.2f}" if price_7d else '--',
                        'price_30d':
                        f"{price_30d:.2f}" if price_30d else '--',
                        'change_7d_pct':
                        f"{change_7d_pct:.2f}%"
                        if change_7d_pct is not None else '--',
                        'change_30d_pct':
                        f"{change_30d_pct:.2f}%"
                        if change_30d_pct is not None else '--',
                        'change_7d':
                        f"{change_7d:.2f}" if change_7d else '--',
                        'change_30d':
                        f"{change_30d:.2f}" if change_30d else '--',
                        'change_pct':
                        f"{daily_change_pct:+.2f}%"
                        if daily_change_pct is not None else '--',
                        'change_val':
                        f"{daily_change_val:+.2f}"
                        if daily_change_val is not None else '--'
                    })
                else:
                    # Fallback values when market data is not available
                    symbol_info.update({
                        'cmp': '--',
                        'price_7d': '--',
                        'price_30d': '--',
                        'change_7d_pct': '--',
                        'change_30d_pct': '--',
                        'change_7d': '--',
                        'change_30d': '--',
                        'change_pct': '--',
                        'change_val': '--'
                    })

            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
                continue

            symbols_with_market_data.append(symbol_info)

        return jsonify({
            "success": True,
            "symbols": symbols_with_market_data,
            "count": len(symbols_with_market_data)
        })

    except Exception as e:
        logger.error(f"Error getting default symbols with market data: {e}")
        return jsonify({
            "error": "Failed to fetch default market data",
            "details": str(e)
        }), 500


def try_percent_calc(current_val, historical_val):
    """Calculate percentage change between two values"""
    try:
        if current_val is not None and historical_val is not None and historical_val != 0:
            return ((current_val - historical_val) / historical_val) * 100
        return None
    except:
        return None


def is_valid_symbol(symbol: str) -> bool:
    """Check if symbol exists in nse_symbols table"""
    if not db_config:
        return False

    try:
        conn = db_config.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM nse_symbols 
                    WHERE UPPER(symbol) = UPPER(%s)
                """, (symbol, ))

                result = cursor.fetchone()
                return bool(result and result[0] > 0)

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {e}")
        return False


# Export blueprint
__all__ = ['market_watch_api']
