"""
Data Analyzer - Analyze and log all data retrieved from trading functions
This tool helps you understand what data is coming from each function
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from Scripts.trading_functions import TradingFunctions

class DataAnalyzer:
    """
    Analyzes and logs all data retrieved from trading functions
    Helps understand data structure and content
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trading_functions = TradingFunctions()
        self.analysis_log = []
        
    def analyze_all_data(self, client):
        """
        Analyze all data retrieved from trading functions
        Returns comprehensive analysis of data structure and content
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'client_type': type(client).__name__,
            'data_sources': {}
        }
        
        # Analyze Dashboard Data
        print("🔍 Analyzing Dashboard Data...")
        dashboard_data = self.analyze_dashboard_data(client)
        analysis['data_sources']['dashboard'] = dashboard_data
        
        # Analyze Positions Data
        print("🔍 Analyzing Positions Data...")
        positions_data = self.analyze_positions_data(client)
        analysis['data_sources']['positions'] = positions_data
        
        # Analyze Holdings Data  
        print("🔍 Analyzing Holdings Data...")
        holdings_data = self.analyze_holdings_data(client)
        analysis['data_sources']['holdings'] = holdings_data
        
        # Analyze Orders Data
        print("🔍 Analyzing Orders Data...")
        orders_data = self.analyze_orders_data(client)
        analysis['data_sources']['orders'] = orders_data
        
        # Analyze Account Limits
        print("🔍 Analyzing Account Limits...")
        limits_data = self.analyze_limits_data(client)
        analysis['data_sources']['limits'] = limits_data
        
        return analysis
    
    def analyze_dashboard_data(self, client) -> Dict[str, Any]:
        """Analyze dashboard data structure and content"""
        try:
            dashboard_data = self.trading_functions.get_dashboard_data(client)
            
            analysis = {
                'function_name': 'get_dashboard_data',
                'data_type': type(dashboard_data).__name__,
                'data_structure': self._analyze_structure(dashboard_data),
                'sample_data': self._get_sample_data(dashboard_data),
                'data_count': self._count_data_items(dashboard_data),
                'fields_available': self._get_fields_list(dashboard_data),
                'status': 'success'
            }
            
            print(f"✅ Dashboard Data Analysis Complete")
            print(f"   - Data Type: {analysis['data_type']}")
            print(f"   - Total Items: {analysis['data_count']}")
            print(f"   - Available Fields: {len(analysis['fields_available'])}")
            
            return analysis
            
        except Exception as e:
            return {
                'function_name': 'get_dashboard_data',
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_positions_data(self, client) -> Dict[str, Any]:
        """Analyze positions data structure and content"""
        try:
            positions_data = self.trading_functions.get_positions(client)
            
            analysis = {
                'function_name': 'get_positions',
                'data_type': type(positions_data).__name__,
                'data_structure': self._analyze_structure(positions_data),
                'sample_data': self._get_sample_data(positions_data),
                'data_count': self._count_data_items(positions_data),
                'fields_available': self._get_fields_list(positions_data),
                'status': 'success'
            }
            
            print(f"✅ Positions Data Analysis Complete")
            print(f"   - Data Type: {analysis['data_type']}")
            print(f"   - Total Items: {analysis['data_count']}")
            print(f"   - Available Fields: {len(analysis['fields_available'])}")
            
            return analysis
            
        except Exception as e:
            return {
                'function_name': 'get_positions',
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_holdings_data(self, client) -> Dict[str, Any]:
        """Analyze holdings data structure and content"""
        try:
            holdings_data = self.trading_functions.get_holdings(client)
            
            analysis = {
                'function_name': 'get_holdings',
                'data_type': type(holdings_data).__name__,
                'data_structure': self._analyze_structure(holdings_data),
                'sample_data': self._get_sample_data(holdings_data),
                'data_count': self._count_data_items(holdings_data),
                'fields_available': self._get_fields_list(holdings_data),
                'status': 'success'
            }
            
            print(f"✅ Holdings Data Analysis Complete")
            print(f"   - Data Type: {analysis['data_type']}")
            print(f"   - Total Items: {analysis['data_count']}")
            print(f"   - Available Fields: {len(analysis['fields_available'])}")
            
            return analysis
            
        except Exception as e:
            return {
                'function_name': 'get_holdings',
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_orders_data(self, client) -> Dict[str, Any]:
        """Analyze orders data structure and content"""
        try:
            orders_data = self.trading_functions.get_orders(client)
            
            analysis = {
                'function_name': 'get_orders',
                'data_type': type(orders_data).__name__,
                'data_structure': self._analyze_structure(orders_data),
                'sample_data': self._get_sample_data(orders_data),
                'data_count': self._count_data_items(orders_data),
                'fields_available': self._get_fields_list(orders_data),
                'status': 'success'
            }
            
            print(f"✅ Orders Data Analysis Complete")
            print(f"   - Data Type: {analysis['data_type']}")
            print(f"   - Total Items: {analysis['data_count']}")
            print(f"   - Available Fields: {len(analysis['fields_available'])}")
            
            return analysis
            
        except Exception as e:
            return {
                'function_name': 'get_orders',
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_limits_data(self, client) -> Dict[str, Any]:
        """Analyze account limits data structure and content"""
        try:
            limits_data = self.trading_functions.get_limits(client)
            
            analysis = {
                'function_name': 'get_limits',
                'data_type': type(limits_data).__name__,
                'data_structure': self._analyze_structure(limits_data),
                'sample_data': self._get_sample_data(limits_data),
                'data_count': self._count_data_items(limits_data),
                'fields_available': self._get_fields_list(limits_data),
                'status': 'success'
            }
            
            print(f"✅ Account Limits Analysis Complete")
            print(f"   - Data Type: {analysis['data_type']}")
            print(f"   - Total Items: {analysis['data_count']}")
            print(f"   - Available Fields: {len(analysis['fields_available'])}")
            
            return analysis
            
        except Exception as e:
            return {
                'function_name': 'get_limits',
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_structure(self, data) -> Dict[str, Any]:
        """Analyze the structure of data"""
        if isinstance(data, dict):
            return {
                'type': 'dictionary',
                'keys': list(data.keys()),
                'nested_structure': {k: type(v).__name__ for k, v in data.items()}
            }
        elif isinstance(data, list):
            return {
                'type': 'list',
                'length': len(data),
                'item_types': [type(item).__name__ for item in data[:5]]  # Sample first 5
            }
        else:
            return {
                'type': type(data).__name__,
                'value': str(data)
            }
    
    def _get_sample_data(self, data, max_items=2):
        """Get sample data for analysis"""
        if isinstance(data, dict):
            return {k: v for k, v in list(data.items())[:max_items]}
        elif isinstance(data, list):
            return data[:max_items]
        else:
            return data
    
    def _count_data_items(self, data) -> int:
        """Count total data items"""
        if isinstance(data, dict):
            return len(data)
        elif isinstance(data, list):
            return len(data)
        else:
            return 1
    
    def _get_fields_list(self, data) -> List[str]:
        """Get list of available fields"""
        fields = []
        
        if isinstance(data, dict):
            fields.extend(data.keys())
            # If there are nested items, get their fields too
            for key, value in data.items():
                if isinstance(value, list) and value:
                    if isinstance(value[0], dict):
                        fields.extend([f"{key}.{subkey}" for subkey in value[0].keys()])
                elif isinstance(value, dict):
                    fields.extend([f"{key}.{subkey}" for subkey in value.keys()])
        elif isinstance(data, list) and data:
            if isinstance(data[0], dict):
                fields.extend(data[0].keys())
        
        return list(set(fields))
    
    def save_analysis_report(self, analysis, filename="data_analysis_report.json"):
        """Save analysis report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"📊 Analysis report saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving report: {str(e)}")
            return False
    
    def print_summary_report(self, analysis):
        """Print a comprehensive summary report"""
        print("\n" + "="*60)
        print("📊 TRADING DATA ANALYSIS SUMMARY")
        print("="*60)
        print(f"Analysis Date: {analysis['timestamp']}")
        print(f"Client Type: {analysis['client_type']}")
        print("")
        
        for source_name, source_data in analysis['data_sources'].items():
            print(f"📋 {source_name.upper()} DATA:")
            print(f"   Function: {source_data.get('function_name', 'N/A')}")
            print(f"   Status: {source_data.get('status', 'N/A')}")
            
            if source_data.get('status') == 'success':
                print(f"   Data Type: {source_data.get('data_type', 'N/A')}")
                print(f"   Item Count: {source_data.get('data_count', 'N/A')}")
                print(f"   Fields Available: {len(source_data.get('fields_available', []))}")
                
                if source_data.get('fields_available'):
                    print(f"   Key Fields: {', '.join(source_data['fields_available'][:10])}")
                    if len(source_data['fields_available']) > 10:
                        print(f"   ... and {len(source_data['fields_available']) - 10} more")
            else:
                print(f"   Error: {source_data.get('error', 'Unknown error')}")
            print("")
        
        print("="*60)