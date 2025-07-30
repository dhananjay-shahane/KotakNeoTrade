from flask import Blueprint, jsonify, request
import logging
from Scripts.external_db_service import SignalsFetcher
from core.database import get_db_connection

# Create blueprint
default_deals_api = Blueprint('default_deals_api', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@default_deals_api.route('/api/default-deals', methods=['GET'])
def get_default_deals():
    """
    Get all default deals data from the default_deals table
    No authentication required - shows all deals for everyone
    """
    try:
        logger.info("📊 Fetching default deals data...")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed")
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'deals': []
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # Query to get all deals from default_deals table
            query = """
            SELECT 
                id,
                symbol,
                seven,
                seven_percent,
                thirty,
                thirty_percent,
                date,
                qty,
                ep,
                cmp,
                pos,
                chan_percent,
                inv,
                tp,
                tpr,
                tva,
                pl,
                qt,
                ed,
                exp,
                pr,
                pp,
                iv,
                ip,
                status,
                created_at,
                updated_at
            FROM default_deals 
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            deals_data = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Convert to list of dictionaries
            deals_list = []
            for row in deals_data:
                deal_dict = dict(zip(column_names, row))
                
                # Format dates
                if deal_dict.get('date'):
                    deal_dict['date'] = str(deal_dict['date'])
                if deal_dict.get('ed'):
                    deal_dict['ed'] = str(deal_dict['ed'])
                if deal_dict.get('created_at'):
                    deal_dict['created_at'] = str(deal_dict['created_at'])
                if deal_dict.get('updated_at'):
                    deal_dict['updated_at'] = str(deal_dict['updated_at'])
                
                # Ensure numeric fields are properly formatted
                numeric_fields = ['seven', 'seven_percent', 'thirty', 'thirty_percent', 
                                'qty', 'ep', 'cmp', 'chan_percent', 'inv', 'tp', 'tpr', 
                                'tva', 'pl', 'qt', 'exp', 'pr', 'pp', 'iv', 'ip']
                
                for field in numeric_fields:
                    if deal_dict.get(field) is not None:
                        try:
                            deal_dict[field] = float(deal_dict[field])
                        except (ValueError, TypeError):
                            deal_dict[field] = 0.0
                
                deals_list.append(deal_dict)
            
            logger.info(f"✅ Successfully fetched {len(deals_list)} default deals")
            
            return jsonify({
                'success': True,
                'message': f'Successfully loaded {len(deals_list)} default deals',
                'deals': deals_list,
                'total_count': len(deals_list)
            })
            
        except Exception as query_error:
            logger.error(f"❌ Database query error: {str(query_error)}")
            return jsonify({
                'success': False,
                'message': f'Database query error: {str(query_error)}',
                'deals': []
            }), 500
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"❌ Error in get_default_deals: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading default deals: {str(e)}',
            'deals': []
        }), 500

@default_deals_api.route('/api/default-deals/sync', methods=['POST'])
def sync_default_deals():
    """
    Sync default deals from admin_trade_signals table
    Copies all data from admin_trade_signals to default_deals
    """
    try:
        logger.info("🔄 Starting default deals sync from admin_trade_signals...")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed")
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # First, get all data from admin_trade_signals
            admin_query = """
            SELECT 
                symbol,
                seven,
                seven_percent,
                thirty,
                thirty_percent,
                date,
                qty,
                ep,
                cmp,
                pos,
                chan_percent,
                inv,
                tp,
                tpr,
                tva,
                pl,
                qt,
                ed,
                exp,
                pr,
                pp,
                iv,
                ip
            FROM admin_trade_signals 
            ORDER BY date DESC
            """
            
            cursor.execute(admin_query)
            admin_data = cursor.fetchall()
            
            if not admin_data:
                logger.warning("⚠️ No data found in admin_trade_signals table")
                return jsonify({
                    'success': False,
                    'message': 'No data found in admin_trade_signals table'
                }), 404
            
            # Clear existing default_deals data
            cursor.execute("DELETE FROM default_deals")
            logger.info("🗑️ Cleared existing default_deals data")
            
            # Insert data into default_deals
            insert_query = """
            INSERT INTO default_deals (
                symbol, seven, seven_percent, thirty, thirty_percent, date,
                qty, ep, cmp, pos, chan_percent, inv, tp, tpr, tva, pl, qt,
                ed, exp, pr, pp, iv, ip, status, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', NOW(), NOW()
            )
            """
            
            synced_count = 0
            for row in admin_data:
                try:
                    cursor.execute(insert_query, row)
                    synced_count += 1
                except Exception as insert_error:
                    logger.warning(f"⚠️ Failed to insert row: {str(insert_error)}")
                    continue
            
            # Commit the transaction
            conn.commit()
            
            logger.info(f"✅ Successfully synced {synced_count} deals to default_deals table")
            
            return jsonify({
                'success': True,
                'message': f'Successfully synced {synced_count} deals from admin_trade_signals',
                'synced_count': synced_count
            })
            
        except Exception as query_error:
            conn.rollback()
            logger.error(f"❌ Database sync error: {str(query_error)}")
            return jsonify({
                'success': False,
                'message': f'Database sync error: {str(query_error)}'
            }), 500
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"❌ Error in sync_default_deals: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error syncing default deals: {str(e)}'
        }), 500

@default_deals_api.route('/api/default-deals/update-cmp', methods=['POST'])
def update_default_deals_cmp():
    """
    Update CMP (Current Market Price) for all deals in default_deals table
    Uses the same price fetching logic as other components
    """
    try:
        logger.info("💰 Starting CMP update for default deals...")
        
        # Initialize signals fetcher for price updates
        signals_fetcher = SignalsFetcher()
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed")
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # Get all symbols from default_deals
            cursor.execute("SELECT DISTINCT symbol FROM default_deals WHERE symbol IS NOT NULL")
            symbols = [row[0] for row in cursor.fetchall()]
            
            if not symbols:
                logger.warning("⚠️ No symbols found in default_deals table")
                return jsonify({
                    'success': False,
                    'message': 'No symbols found in default_deals table'
                }), 404
            
            updated_count = 0
            failed_symbols = []
            
            # Update CMP for each symbol
            for symbol in symbols:
                try:
                    # Get current market price using signals fetcher
                    cmp = signals_fetcher.get_cmp_from_symbols_table(symbol)
                    
                    if cmp and cmp > 0:
                        # Update CMP in default_deals table
                        update_query = """
                        UPDATE default_deals 
                        SET cmp = %s, updated_at = NOW() 
                        WHERE symbol = %s
                        """
                        cursor.execute(update_query, (cmp, symbol))
                        updated_count += 1
                        logger.info(f"📈 Updated {symbol}: CMP = {cmp}")
                    else:
                        failed_symbols.append(symbol)
                        logger.warning(f"⚠️ Failed to get CMP for {symbol}")
                        
                except Exception as symbol_error:
                    failed_symbols.append(symbol)
                    logger.error(f"❌ Error updating {symbol}: {str(symbol_error)}")
                    continue
            
            # Commit the transaction
            conn.commit()
            
            logger.info(f"✅ Successfully updated CMP for {updated_count} symbols")
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated CMP for {updated_count} symbols',
                'updated_count': updated_count,
                'failed_symbols': failed_symbols,
                'total_symbols': len(symbols)
            })
            
        except Exception as query_error:
            conn.rollback()
            logger.error(f"❌ Database update error: {str(query_error)}")
            return jsonify({
                'success': False,
                'message': f'Database update error: {str(query_error)}'
            }), 500
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"❌ Error in update_default_deals_cmp: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating CMP: {str(e)}'
        }), 500

@default_deals_api.route('/api/default-deals/stats', methods=['GET'])
def get_default_deals_stats():
    """
    Get statistics for default deals
    """
    try:
        logger.info("📊 Fetching default deals statistics...")
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Database connection failed")
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'stats': {}
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # Get basic stats
            stats_query = """
            SELECT 
                COUNT(*) as total_deals,
                COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_deals,
                COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_deals,
                SUM(CASE WHEN inv IS NOT NULL THEN inv ELSE 0 END) as total_investment,
                SUM(CASE WHEN tva IS NOT NULL THEN tva ELSE 0 END) as total_current_value,
                SUM(CASE WHEN pl IS NOT NULL THEN pl ELSE 0 END) as total_pnl,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM default_deals
            """
            
            cursor.execute(stats_query)
            stats_row = cursor.fetchone()
            
            stats = {
                'total_deals': stats_row[0] or 0,
                'active_deals': stats_row[1] or 0,
                'closed_deals': stats_row[2] or 0,
                'total_investment': float(stats_row[3] or 0),
                'total_current_value': float(stats_row[4] or 0),
                'total_pnl': float(stats_row[5] or 0),
                'unique_symbols': stats_row[6] or 0
            }
            
            logger.info(f"✅ Successfully fetched default deals stats: {stats}")
            
            return jsonify({
                'success': True,
                'message': 'Successfully loaded default deals statistics',
                'stats': stats
            })
            
        except Exception as query_error:
            logger.error(f"❌ Database stats query error: {str(query_error)}")
            return jsonify({
                'success': False,
                'message': f'Database stats query error: {str(query_error)}',
                'stats': {}
            }), 500
            
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logger.error(f"❌ Error in get_default_deals_stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error loading stats: {str(e)}',
            'stats': {}
        }), 500