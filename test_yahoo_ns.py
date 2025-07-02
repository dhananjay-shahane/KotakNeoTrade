#!/usr/bin/env python3
"""
Test script for Yahoo Finance .NS suffix functionality
"""
import sys
import os
sys.path.append('.')

from Scripts.yahoo_finance_service import YahooFinanceService

def test_yahoo_ns_functionality():
    """Test the improved Yahoo Finance service with .NS suffix"""
    print("Testing Yahoo Finance with dynamic .NS suffix...")
    
    # Create service instance
    yahoo_service = YahooFinanceService()
    
    # Test symbols
    test_symbols = [
        'NIFTYBEES',  # ETF
        'RELIANCE',   # Large cap stock
        'TCS',        # Tech stock
        'GOLDBEES',   # ETF
        'CONSUMBEES', # ETF
        'HDFCBANK'    # Bank stock
    ]
    
    print("Testing symbol suffix generation:")
    for symbol in test_symbols:
        yahoo_symbol = yahoo_service.get_yahoo_symbol(symbol)
        print(f"  {symbol} -> {yahoo_symbol}")
    
    print("\nTesting live price fetching:")
    for symbol in test_symbols[:3]:  # Test first 3 only
        try:
            print(f"\nFetching price for {symbol}...")
            price_data = yahoo_service.get_stock_price(symbol)
            if price_data:
                print(f"  ✅ {symbol}: ₹{price_data['current_price']} (Source: {'Real' if price_data.get('timestamp') else 'Fallback'})")
                print(f"     Change: {price_data.get('change_percent', 0):.2f}%")
            else:
                print(f"  ❌ {symbol}: No data available")
        except Exception as e:
            print(f"  ❌ {symbol}: Error - {e}")

if __name__ == "__main__":
    test_yahoo_ns_functionality()