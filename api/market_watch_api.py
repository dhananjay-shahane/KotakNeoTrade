"""
Market Watch API for Symbol Management
Handles symbol search, filtering, and watchlist operations using nse_symbols table
"""
from flask import Blueprint, request, jsonify, session
import logging
import psycopg2.extras
from config.database_config import DatabaseConfig
from Scripts.user_market_watch_service import UserMarketWatchService

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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get unique companies
                cursor.execute("SELECT DISTINCT company FROM nse_symbols WHERE company IS NOT NULL ORDER BY company LIMIT 100")
                companies = [row['company'] for row in cursor.fetchall()]
                
                # Get unique sectors
                cursor.execute("SELECT DISTINCT sector FROM nse_symbols WHERE sector IS NOT NULL ORDER BY sector")
                sectors = [row['sector'] for row in cursor.fetchall()]
                
                # Get unique sub_sectors
                cursor.execute("SELECT DISTINCT sub_sector FROM nse_symbols WHERE sub_sector IS NOT NULL ORDER BY sub_sector")
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
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT symbol, company, sector, sub_sector, nifty, nifty_500, etf
                    FROM nse_symbols 
                    WHERE UPPER(symbol) = UPPER(%s)
                """, (symbol,))
                
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
                
                return jsonify({
                    "success": True,
                    "symbol": symbol_details
                })
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting symbol details: {e}")
        return jsonify({"error": "Failed to get symbol details"}), 500

@market_watch_api.route('/api/market-watch/user-symbols', methods=['GET', 'POST', 'DELETE'])
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
            return jsonify({"error": "Invalid symbol or not found in market data"}), 404
            
        # Add symbol to user's watchlist
        success = user_watchlist_service.add_symbol_to_watchlist(username, symbol)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Symbol {symbol} added to market watch",
                "symbol": symbol
            })
        else:
            return jsonify({"error": "Failed to add symbol or symbol already exists"}), 400
    
    elif request.method == 'DELETE':
        json_data = request.json or {}
        symbol = json_data.get('symbol', '').upper()
        
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400
            
        # Remove symbol from user's watchlist
        success = user_watchlist_service.remove_symbol_from_watchlist(username, symbol)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Symbol {symbol} removed from market watch",
                "symbol": symbol
            })
        else:
            return jsonify({"error": "Failed to remove symbol or symbol not found"}), 400

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
                cursor.execute("""
                    SELECT COUNT(*) FROM nse_symbols 
                    WHERE UPPER(symbol) = UPPER(%s)
                """, (symbol,))
                
                result = cursor.fetchone()
                return result and result[0] > 0
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {e}")
        return False

# Export blueprint
__all__ = ['market_watch_api']