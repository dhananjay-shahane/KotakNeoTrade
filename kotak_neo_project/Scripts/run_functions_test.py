#!/usr/bin/env python3
"""
Functions Data Runner - Test and view output from all functions
This script allows you to run each function individually and see the data structure
"""
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from Scripts.neo_client import NeoClient
from Scripts.trading_functions import TradingFunctions
from Scripts.data_analyzer import DataAnalyzer

def print_separator(title):
    """Print a formatted separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_data_summary(data, title):
    """Print a summary of the data structure"""
    print(f"\n📋 {title}")
    print("-" * 50)
    
    if isinstance(data, dict):
        print(f"Type: Dictionary")
        print(f"Keys: {list(data.keys())}")
        print(f"Total Items: {len(data)}")
        
        # Show sample data for each key
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  {key}: List with {len(value)} items")
                if value and isinstance(value[0], dict):
                    print(f"    Sample item keys: {list(value[0].keys())}")
            elif isinstance(value, dict):
                print(f"  {key}: Dictionary with {len(value)} items")
                print(f"    Keys: {list(value.keys())}")
            else:
                print(f"  {key}: {type(value).__name__} = {value}")
    
    elif isinstance(data, list):
        print(f"Type: List")
        print(f"Length: {len(data)}")
        if data:
            print(f"First item type: {type(data[0]).__name__}")
            if isinstance(data[0], dict):
                print(f"First item keys: {list(data[0].keys())}")
    else:
        print(f"Type: {type(data).__name__}")
        print(f"Value: {data}")

def save_data_to_file(data, filename):
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving to {filename}: {e}")

def main():
    """Main function to run all tests"""
    print_separator("TRADING FUNCTIONS DATA RUNNER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize clients
    print("\n🔧 Initializing Neo API client...")
    neo_client = NeoClient()
    
    try:
        # Login to get client session
        print("🔐 Attempting login...")
        client = neo_client.login()
        if not client:
            print("❌ Login failed. Please check your credentials.")
            return
        
        print("✅ Login successful!")
        
        # Initialize trading functions
        trading_functions = TradingFunctions()
        data_analyzer = DataAnalyzer()
        
        # Test each function individually
        print_separator("1. DASHBOARD DATA")
        try:
            dashboard_data = trading_functions.get_dashboard_data(client)
            print_data_summary(dashboard_data, "Dashboard Data")
            save_data_to_file(dashboard_data, "output_dashboard_data.json")
        except Exception as e:
            print(f"❌ Error fetching dashboard data: {e}")
        
        print_separator("2. POSITIONS DATA")
        try:
            positions_data = trading_functions.get_positions(client)
            print_data_summary(positions_data, "Positions Data")
            save_data_to_file(positions_data, "output_positions_data.json")
        except Exception as e:
            print(f"❌ Error fetching positions data: {e}")
        
        print_separator("3. HOLDINGS DATA")
        try:
            holdings_data = trading_functions.get_holdings(client)
            print_data_summary(holdings_data, "Holdings Data")
            save_data_to_file(holdings_data, "output_holdings_data.json")
        except Exception as e:
            print(f"❌ Error fetching holdings data: {e}")
        
        print_separator("4. ORDERS DATA")
        try:
            orders_data = trading_functions.get_orders(client)
            print_data_summary(orders_data, "Orders Data")
            save_data_to_file(orders_data, "output_orders_data.json")
        except Exception as e:
            print(f"❌ Error fetching orders data: {e}")
        
        print_separator("5. ACCOUNT LIMITS DATA")
        try:
            limits_data = trading_functions.get_limits(client)
            print_data_summary(limits_data, "Account Limits Data")
            save_data_to_file(limits_data, "output_limits_data.json")
        except Exception as e:
            print(f"❌ Error fetching limits data: {e}")
        
        print_separator("6. COMPREHENSIVE ANALYSIS")
        try:
            analysis = data_analyzer.analyze_all_data(client)
            data_analyzer.print_summary_report(analysis)
            save_data_to_file(analysis, "complete_data_analysis.json")
        except Exception as e:
            print(f"❌ Error running comprehensive analysis: {e}")
        
        print_separator("SUMMARY")
        print("✅ All functions have been tested")
        print("📁 Data files saved:")
        print("   - output_dashboard_data.json")
        print("   - output_positions_data.json")
        print("   - output_holdings_data.json")
        print("   - output_orders_data.json")
        print("   - output_limits_data.json")
        print("   - complete_data_analysis.json")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()