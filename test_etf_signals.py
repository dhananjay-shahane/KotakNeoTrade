
#!/usr/bin/env python3
"""Test script to verify ETF signals data loading"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_etf_signals():
    """Test ETF signals data loading from various sources"""
    
    print("🔍 Testing ETF signals data loading...")
    
    # Test 1: External database service
    try:
        from Scripts.external_db_service import get_etf_signals_from_external_db
        signals = get_etf_signals_from_external_db()
        print(f"✓ External DB: Found {len(signals) if signals else 0} signals")
        if signals and len(signals) > 0:
            print(f"  Sample signal: {signals[0].get('symbol', 'Unknown')} - {signals[0].get('entry_price', 0)}")
    except Exception as e:
        print(f"❌ External DB error: {e}")
    
    # Test 2: Local database connection
    try:
        from core.database import get_db_connection
        import psycopg2.extras
        
        conn = get_db_connection()
        if conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM admin_trade_signals")
                result = cursor.fetchone()
                print(f"✓ Local DB: Found {result['count']} signals in admin_trade_signals table")
                
                # Get sample data
                cursor.execute("SELECT * FROM admin_trade_signals LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"  Sample: {sample.get('symbol', 'Unknown')} - {sample.get('entry_price', 0)}")
            conn.close()
    except Exception as e:
        print(f"❌ Local DB error: {e}")
    
    # Test 3: API endpoint
    try:
        import requests
        response = requests.get('http://127.0.0.1:5000/api/etf-signals-data')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API endpoint: {data.get('total', 0)} signals returned")
            if data.get('data'):
                print(f"  Sample: {data['data'][0].get('symbol', 'Unknown')} - {data['data'][0].get('ep', 0)}")
        else:
            print(f"❌ API endpoint error: Status {response.status_code}")
    except Exception as e:
        print(f"❌ API test error: {e}")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_etf_signals()
