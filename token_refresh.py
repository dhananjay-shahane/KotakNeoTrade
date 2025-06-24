
#!/usr/bin/env python3
"""
Token refresh utility for Kotak Neo API
Use this script to get fresh tokens when 2FA is required
"""

import logging
from neo_client import NeoClient
from session_manager import SessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refresh_tokens_interactive():
    """Interactive token refresh process"""
    try:
        print("\n🔐 Kotak Neo Token Refresh")
        print("=" * 40)
        print("If you're getting '2FA required' errors, please:")
        print("1. Login to Kotak Neo mobile app/website")
        print("2. Complete 2FA authentication")
        print("3. Get fresh access tokens")
        print("4. Enter them below\n")
        
        access_token = input("New Access Token: ").strip()
        session_token = input("New Session Token: ").strip()
        sid = input("SID (optional): ").strip()
        ucc = input("UCC: ").strip()
        
        if not access_token or not session_token:
            logger.error("❌ Access Token and Session Token are required")
            return False
        
        # Test the new tokens
        neo_client = NeoClient()
        client = neo_client.initialize_client_with_tokens(access_token, session_token, sid)
        
        if client:
            # Store the validated tokens
            session_manager = SessionManager()
            session_data = {
                'access_token': access_token,
                'session_token': session_token,
                'sid': sid if sid else None,
                'ucc': ucc
            }
            
            if session_manager.store_session('default_user', session_data):
                logger.info("✅ New tokens validated and stored successfully!")
                logger.info("You can now use the application without 2FA errors.")
                return True
            else:
                logger.error("❌ Failed to store new tokens")
                return False
        else:
            logger.error("❌ Failed to validate new tokens. Please check if 2FA is completed.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error refreshing tokens: {e}")
        return False

if __name__ == "__main__":
    refresh_tokens_interactive()
