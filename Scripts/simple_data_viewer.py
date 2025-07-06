#!/usr/bin/env python3
"""
Simple Data Viewer - View output from trading functions
Run this to see what data is being retrieved from each function
"""
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import from existing session if available
import flask
from flask import session

def get_current_session_client():
    """Get client from current Flask session"""
    try:
        # Try to get client from Flask session
        with flask.Flask(__name__).app_context():
            # This won't work outside of Flask context, but we'll handle it
            pass
    except:
        pass
    
    # Return None if no session available
    return None

def view_function_data(function_name, data):
    """Display function data in a readable format"""
    print(f"\n📋 {function_name.upper()} DATA")
    print("-" * 60)
    
    if isinstance(data, dict):
        print(f"📊 Type: Dictionary")
        print(f"📊 Keys: {list(data.keys())}")
        print(f"📊 Total Items: {len(data)}")
        print()
        
        for key, value in data.items():
            if isinstance(value, list):
                print(f"🔸 {key}: List with {len(value)} items")
                if value and isinstance(value[0], dict):
                    print(f"   Sample fields: {list(value[0].keys())}")
                    if len(value) > 0:
                        print(f"   First item: {json.dumps(value[0], indent=2, default=str)[:200]}...")
                print()
            elif isinstance(value, dict):
                print(f"🔸 {key}: Dictionary with {len(value)} items")
                print(f"   Keys: {list(value.keys())}")
                print(f"   Sample: {json.dumps(value, indent=2, default=str)[:200]}...")
                print()
            else:
                print(f"🔸 {key}: {type(value).__name__} = {value}")
                print()
    
    elif isinstance(data, list):
        print(f"📊 Type: List")
        print(f"📊 Length: {len(data)}")
        if data:
            print(f"📊 First item type: {type(data[0]).__name__}")
            if isinstance(data[0], dict):
                print(f"📊 Available fields: {list(data[0].keys())}")
                print(f"📊 Sample item:")
                print(json.dumps(data[0], indent=2, default=str)[:500])
                print()
    else:
        print(f"📊 Type: {type(data).__name__}")
        print(f"📊 Value: {data}")
        print()

def main():
    """Main function to demonstrate data viewing"""
    print("=" * 80)
    print("📊 TRADING FUNCTIONS DATA VIEWER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Import trading functions
    from Scripts.trading_functions import TradingFunctions
    
    # Create instance
    trading_functions = TradingFunctions()
    
    print("This tool shows you the structure of data from each trading function.")
    print("To see live data, you need to run this when your trading session is active.")
    print()
    
    # Show what each function returns
    print("📋 AVAILABLE FUNCTIONS AND THEIR DATA:")
    print("-" * 60)
    
    functions_info = {
        "get_dashboard_data": {
            "description": "Complete dashboard with positions, holdings, orders, and limits",
            "typical_structure": {
                "positions": "List of current trading positions",
                "holdings": "List of long-term holdings",
                "recent_orders": "List of recent order executions",
                "limits": "Account trading limits and margins",
                "summary": "Portfolio summary with totals"
            }
        },
        "get_positions": {
            "description": "Current trading positions only",
            "typical_structure": "List of position objects with fields like symbol, quantity, pnl, etc."
        },
        "get_holdings": {
            "description": "Long-term holdings only", 
            "typical_structure": "List of holding objects with fields like symbol, quantity, value, etc."
        },
        "get_orders": {
            "description": "Recent and pending orders",
            "typical_structure": "List of order objects with fields like symbol, side, quantity, status, etc."
        },
        "get_limits": {
            "description": "Account limits and margin information",
            "typical_structure": "Dictionary with available cash, margin limits, etc."
        }
    }
    
    for func_name, info in functions_info.items():
        print(f"\n🔹 {func_name}()")
        print(f"   Description: {info['description']}")
        print(f"   Structure: {info['typical_structure']}")
    
    print("\n" + "=" * 80)
    print("📝 TO SEE LIVE DATA:")
    print("=" * 80)
    print("1. Make sure your trading application is running")
    print("2. Login to your trading account") 
    print("3. Go to: https://your-app-url/data-analysis")
    print("4. Click 'Analyze All Data' to see live data structure")
    print("5. Or run this script from within an active Flask session")
    print()
    
    print("📁 DATA FILES CREATED:")
    print("When you run the data analysis, these files will be created:")
    print("   - output_dashboard_data.json")
    print("   - output_positions_data.json") 
    print("   - output_holdings_data.json")
    print("   - output_orders_data.json")
    print("   - output_limits_data.json")
    print("   - complete_data_analysis.json")
    print()
    
    print("🔧 SAMPLE DATA STRUCTURE:")
    print("Here's what typical data looks like:")
    print()
    
    # Show sample data structures
    sample_position = {
        "symbol": "RELIANCE",
        "quantity": 100,
        "buyPrice": 2500.00,
        "currentPrice": 2550.00,
        "pnl": 5000.00,
        "pnlPercent": 2.0
    }
    
    sample_holding = {
        "symbol": "TCS",
        "quantity": 50,
        "avgPrice": 3200.00,
        "currentPrice": 3350.00,
        "totalValue": 167500.00,
        "dayChange": 150.00
    }
    
    view_function_data("Sample Position", [sample_position])
    view_function_data("Sample Holding", [sample_holding])
    
    print("=" * 80)
    print("✅ Data viewer information complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()