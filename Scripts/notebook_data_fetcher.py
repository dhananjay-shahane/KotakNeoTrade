"""
Notebook Data Fetcher - Extract real-time trading data from Jupyter notebook style sources
"""
import os
import pandas as pd
import json
import requests
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env', override=True)
try:
    from neo_api_client import NeoAPI
    try:
        from neo_api_client import BaseUrl
    except ImportError:
        # BaseUrl might be in a different module or not available
        BaseUrl = None
except ImportError:
    NeoAPI = None
    BaseUrl = None

class NotebookDataFetcher:
    """Fetch real-time trading data using notebook-style configuration"""
    
    def __init__(self):
        self.client = None
        self.config = {
            'MOBILE_NUMBER': os.environ.get('KOTAK_NEO_MOBILE_NUMBER', "+919372209322"),
            'UCC': os.environ.get('KOTAK_NEO_UCC', "ZHZ3J"), 
            'CONSUMER_KEY': os.environ.get('KOTAK_NEO_CONSUMER_KEY', "4OKP7bOfI5ozzCB1EI4a6DOIyJsa"),
            'CONSUMER_SECRET': os.environ.get('KOTAK_NEO_CONSUMER_SECRET', "cnLm3ZSJVLCOPiwTk4xAJw5G8v0a"),
            'NEO_FIN_KEY': os.environ.get('KOTAK_NEO_FIN_KEY', "neotradeapi"),
            'MPIN': os.environ.get('KOTAK_NEO_MPIN', "484848"),
            'ENVIRONMENT': os.environ.get('KOTAK_NEO_ENVIRONMENT', "prod")
        }
        self.session_data = {}
        
    def initialize_client(self):
        """Initialize Neo API client using notebook configuration"""
        try:
            if NeoAPI is None:
                logging.warning("Neo API client not available, using CSV data")
                return False
                
            # Try to initialize without BaseUrl if not available
            if BaseUrl is not None:
                try:
                    base_url = BaseUrl(ucc=self.config['UCC']).get_base_url()
                except:
                    base_url = os.environ.get('KOTAK_NEO_BASE_URL', 'https://gw-napi.kotaksecurities.com/')
            else:
                base_url = os.environ.get('KOTAK_NEO_BASE_URL', 'https://gw-napi.kotaksecurities.com/')
            
            logging.info(f"Base URL: {base_url}")
            
            # Initialize client with available parameters
            self.client = NeoAPI(
                consumer_key=self.config['CONSUMER_KEY'],
                consumer_secret=self.config['CONSUMER_SECRET'],
                environment=self.config['ENVIRONMENT'],
                access_token=None,
                neo_fin_key=self.config['NEO_FIN_KEY']
            )
            
            logging.info("Neo API client initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error initializing Neo API client: {str(e)}")
            return False
    
    def authenticate_with_stored_session(self):
        """Authenticate using stored session tokens if available"""
        try:
            # Try to use stored session data from previous notebook execution
            stored_tokens = self.get_stored_session_tokens()
            if stored_tokens:
                self.session_data = stored_tokens
                logging.info("Using stored session tokens")
                return True
            
            logging.warning("No valid stored session found")
            return False
            
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return False
    
    def get_stored_session_tokens(self):
        """Extract session tokens from notebook execution results"""
        # This would contain the actual session tokens from the notebook
        # For now, return None to indicate no stored session
        return None
    
    def fetch_positions_data(self):
        """Fetch current positions using notebook-style API calls"""
        try:
            if not self.client:
                if not self.initialize_client():
                    return []
            
            if not self.authenticate_with_stored_session():
                logging.warning("Authentication required - authentic data only")
                return []
            
            # Fetch positions from API
            positions = self.client.positions()
            logging.info(f"Retrieved {len(positions) if positions else 0} positions")
            
            return self.format_positions_data(positions)
            
        except Exception as e:
            logging.error(f"Error fetching positions: {str(e)}")
            return []
    
    def fetch_holdings_data(self):
        """Fetch holdings data"""
        try:
            if not self.client:
                return []
                
            holdings = self.client.holdings()
            logging.info(f"Retrieved {len(holdings) if holdings else 0} holdings")
            
            return self.format_holdings_data(holdings)
            
        except Exception as e:
            logging.error(f"Error fetching holdings: {str(e)}")
            return []
    
    def fetch_orders_data(self):
        """Fetch order book data"""
        try:
            if not self.client:
                return []
                
            orders = self.client.order_report()
            logging.info(f"Retrieved {len(orders) if orders else 0} orders")
            
            return self.format_orders_data(orders)
            
        except Exception as e:
            logging.error(f"Error fetching orders: {str(e)}")
            return []
    
    def fetch_limits_data(self):
        """Fetch account limits"""
        try:
            if not self.client:
                return {}
                
            limits = self.client.limits()
            logging.info("Retrieved account limits")
            
            return self.format_limits_data(limits)
            
        except Exception as e:
            logging.error(f"Error fetching limits: {str(e)}")
            return {}
    
    def format_positions_data(self, positions):
        """Format positions data to standard structure"""
        formatted = []
        
        if not positions:
            return formatted
            
        for pos in positions:
            try:
                formatted.append({
                    'symbol': pos.get('trdSym', ''),
                    'product': pos.get('prod', ''),
                    'quantity': int(pos.get('flBuyQty', 0)) - int(pos.get('flSellQty', 0)),
                    'avg_price': float(pos.get('buyAmt', 0)) / max(int(pos.get('flBuyQty', 1)), 1),
                    'ltp': float(pos.get('stkPrc', 0)),
                    'pnl': float(pos.get('unrealizedPL', 0)),
                    'pnl_percent': 0.0,  # Calculate based on avg_price and ltp
                    'segment': pos.get('exSeg', '')
                })
            except (ValueError, TypeError):
                continue
                
        return formatted
    
    def format_holdings_data(self, holdings):
        """Format holdings data"""
        formatted = []
        
        if not holdings:
            return formatted
            
        for holding in holdings:
            try:
                formatted.append({
                    'symbol': holding.get('trdSym', ''),
                    'quantity': int(holding.get('holdQty', 0)),
                    'avg_price': float(holding.get('avgPrice', 0)),
                    'ltp': float(holding.get('ltp', 0)),
                    'value': float(holding.get('mktValue', 0)),
                    'pnl': float(holding.get('pnl', 0)),
                    'pnl_percent': float(holding.get('pnlPerc', 0))
                })
            except (ValueError, TypeError):
                continue
                
        return formatted
    
    def format_orders_data(self, orders):
        """Format orders data"""
        formatted = []
        
        if not orders:
            return formatted
            
        for order in orders:
            try:
                formatted.append({
                    'order_id': order.get('nOrdNo', ''),
                    'symbol': order.get('trdSym', ''),
                    'side': order.get('trnsTp', ''),
                    'quantity': int(order.get('qty', 0)),
                    'price': float(order.get('prc', 0)),
                    'status': order.get('ordSt', ''),
                    'timestamp': order.get('hsUpTm', '')
                })
            except (ValueError, TypeError):
                continue
                
        return formatted
    
    def format_limits_data(self, limits):
        """Format limits data"""
        if not limits:
            return {}
            
        return {
            'available_cash': float(limits.get('cash', {}).get('availableBalance', 0)),
            'total_margin': float(limits.get('margin', {}).get('totalMargin', 0)),
            'used_margin': float(limits.get('margin', {}).get('usedMargin', 0)),
            'available_margin': float(limits.get('margin', {}).get('availableMargin', 0))
        }
    
    def get_comprehensive_dashboard_data(self):
        """Get all dashboard data in one call"""
        try:
            positions = self.fetch_positions_data()
            holdings = self.fetch_holdings_data()
            orders = self.fetch_orders_data()
            limits = self.fetch_limits_data()
            
            # Calculate summary metrics
            total_pnl = sum(pos['pnl'] for pos in positions)
            total_value = sum(pos.get('value', pos['quantity'] * pos['ltp']) for pos in positions)
            
            return {
                'positions': positions,
                'holdings': holdings,
                'recent_orders': orders[-10:] if orders else [],  # Last 10 orders
                'limits': limits,
                'summary': {
                    'total_positions': len(positions),
                    'total_holdings': len(holdings),
                    'total_orders': len(orders),
                    'total_pnl': total_pnl,
                    'total_value': total_value,
                    'available_cash': limits.get('available_cash', 0)
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting comprehensive dashboard data: {str(e)}")
            return {
                'positions': [],
                'holdings': [],
                'recent_orders': [],
                'limits': {},
                'summary': {
                    'total_positions': 0,
                    'total_holdings': 0,
                    'total_orders': 0,
                    'total_pnl': 0.0,
                    'total_value': 0.0,
                    'available_cash': 0.0
                }
            }