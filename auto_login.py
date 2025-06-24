
#!/usr/bin/env python3
"""
Standalone script to test and maintain Kotak Neo API sessions
This script can be run independently to verify authentication
"""

import sys
import os
import logging
from session_manager import SessionManager
from neo_client import NeoClient

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stored_session():
    """Test if stored session is valid"""
    try:
        session_manager = SessionManager()
        neo_client = NeoClient()
        
        # Get stored session
        stored_session = session_manager.get_valid_session()
        if not stored_session:
            logger.error("❌ No valid stored session found")
            return False
        
        logger.info("📱 Found stored session, testing authentication...")
        
        # Initialize client with stored tokens
        client = neo_client.initialize_client_with_tokens(
            stored_session['access_token'],
            stored_session['session_token'],
            stored_session['sid']
        )
        
        if client:
            logger.info("✅ Authentication successful with stored session!")
            
            # Test API call
            try:
                # Try a simple API call to verify session
                limits = client.limits()
                if limits:
                    logger.info("✅ API call successful - session is active")
                    return True
                else:
                    logger.warning("⚠️ API call returned empty - session may be expired")
            except Exception as e:
                logger.error(f"❌ API call failed: {e}")
                # Remove invalid session
                session_manager.remove_session('default_user')
        else:
            logger.error("❌ Failed to initialize client with stored tokens")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing stored session: {e}")
        return False

def store_new_session():
    """Store new session interactively"""
    try:
        session_manager = SessionManager()
        
        print("\n🔐 Enter your Kotak Neo tokens:")
        access_token = input("Access Token: ").strip()
        session_token = input("Session Token: ").strip()
        sid = input("SID (optional): ").strip()
        ucc = input("UCC: ").strip()
        
        if not access_token or not session_token:
            logger.error("❌ Access Token and Session Token are required")
            return False
        
        # Store session
        session_data = {
            'access_token': access_token,
            'session_token': session_token,
            'sid': sid if sid else None,
            'ucc': ucc
        }
        
        if session_manager.store_session('default_user', session_data):
            logger.info("✅ Session stored successfully!")
            return True
        else:
            logger.error("❌ Failed to store session")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error storing session: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Kotak Neo Auto-Login Manager")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "store":
        # Store new session
        store_new_session()
    else:
        # Test existing session
        if not test_stored_session():
            print("\n💡 Run 'python auto_login.py store' to store new tokens")
