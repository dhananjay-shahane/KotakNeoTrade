
#!/usr/bin/env python3
"""
Test script to verify AUTOIETF CMP update functionality - REAL DATA ONLY
"""

import requests
import json
import sys
import time

def test_autoietf_update():
    """Test updating AUTOIETF CMP specifically with REAL data"""
    print("🧪 Testing AUTOIETF REAL CMP Update")
    print("=" * 50)
    
    # Test the Google Finance endpoint directly
    symbol = "AUTOIETF"
    url = f"http://localhost:5000/api/google-finance/force-update-symbol/{symbol}"
    
    try:
        print(f"🔄 Sending request to: {url}")
        print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(url, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"💰 REAL Price: ₹{data.get('price', 'N/A')}")
            print(f"📊 Updated Rows: {data.get('updated_rows', 0)}")
            print(f"📝 Message: {data.get('message', 'N/A')}")
            
            # Verify this is real data
            price = data.get('price')
            if price and price > 0:
                print(f"✅ CONFIRMED: Real market price ₹{price} fetched successfully!")
            else:
                print("❌ WARNING: No real price data returned")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:5000")
    except requests.exceptions.Timeout:
        print("⏰ Request Timeout: Server took too long to respond")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_bulk_update():
    """Test bulk CMP update for all symbols"""
    print("\n🔄 Testing Bulk CMP Update")
    print("=" * 50)
    
    url = "http://localhost:5000/api/google-finance/update-etf-cmp"
    
    try:
        print(f"🔄 Sending bulk update request to: {url}")
        response = requests.post(url, json={}, timeout=60)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"📊 Total Updated: {data.get('updated_count', 0)}")
            print(f"🎯 Successful Updates: {data.get('successful_updates', 0)}")
            print(f"⏱️ Duration: {data.get('duration', 0):.2f} seconds")
            
            # Show individual results for verification
            results = data.get('results', {})
            if results:
                print("\n📈 Individual Symbol Results:")
                for symbol, result in list(results.items())[:5]:  # Show first 5
                    if result.get('success'):
                        print(f"  ✅ {symbol}: ₹{result.get('price', 'N/A')}")
                    else:
                        print(f"  ❌ {symbol}: Failed")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_autoietf_update()
    test_bulk_update()
