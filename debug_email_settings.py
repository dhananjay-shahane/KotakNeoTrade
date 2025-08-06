#!/usr/bin/env python3
"""
Debug script to test email settings functionality
This script will help identify why state persistence is not working
"""

import requests
import json

# Test email settings API endpoints
def test_email_settings():
    base_url = "https://47481321-fbd8-40ec-904c-e65fd0f7600e-00-136w95rmq2coi.riker.replit.dev"
    
    print("🔍 Testing Email Settings API")
    print("=" * 50)
    
    # Test GET endpoint without authentication
    print("1. Testing GET /api/email-settings (no auth):")
    response = requests.get(f"{base_url}/api/email-settings")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test the settings page directly
    print("2. Testing /settings page:")
    try:
        response = requests.get(f"{base_url}/settings")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Settings page loads successfully")
        else:
            print("Settings page redirects or has issues")
    except Exception as e:
        print(f"Error accessing settings: {e}")
    
    print()
    print("🔍 Analysis Complete")

if __name__ == "__main__":
    test_email_settings()