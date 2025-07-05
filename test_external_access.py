#!/usr/bin/env python3
"""Test external domain access for webview"""
import requests
import os
import sys

def test_external_access():
    """Test if the application is accessible from the external domain"""
    domain = os.environ.get('REPLIT_DOMAINS')
    if not domain:
        print("❌ REPLIT_DOMAINS not found")
        return False
    
    test_url = f"https://{domain}/test"
    health_url = f"https://{domain}/health"
    
    print(f"Testing external access to: {domain}")
    
    try:
        # Test health endpoint
        print(f"Testing: {health_url}")
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Health endpoint works: {response.status_code}")
        else:
            print(f"⚠️ Health endpoint returned: {response.status_code}")
            
        # Test simple page
        print(f"Testing: {test_url}")
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Test page works: {response.status_code}")
            print(f"Content preview: {response.text[:100]}")
            return True
        else:
            print(f"❌ Test page failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_external_access()
    sys.exit(0 if success else 1)