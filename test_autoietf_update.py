
#!/usr/bin/env python3
"""
Test script to verify AUTOIETF CMP update functionality
"""

import requests
import json
import sys

def test_autoietf_update():
    """Test updating AUTOIETF CMP specifically"""
    print("🧪 Testing AUTOIETF CMP Update")
    print("=" * 50)
    
    # Test the force update endpoint
    symbol = "AUTOIETF"
    url = f"http://localhost:5000/api/google-finance/force-update-symbol/{symbol}"
    
    try:
        print(f"🔄 Sending request to: {url}")
        response = requests.post(url, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"💰 Price: ₹{data.get('price', 'N/A')}")
            print(f"📊 Updated Rows: {data.get('updated_rows', 0)}")
            print(f"📝 Message: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:5000")
    except requests.exceptions.Timeout:
        print("⏰ Request Timeout: Server took too long to respond")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_autoietf_update()
