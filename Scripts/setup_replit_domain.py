
#!/usr/bin/env python3
"""
Script to help configure proper Replit domain settings
"""
import os

def setup_replit_domain():
    """Configure environment for Replit deployment"""
    print("🔧 Configuring Replit Domain Settings...")
    
    # Get current Replit domain
    replit_domain = os.environ.get('REPLIT_DOMAINS')
    if replit_domain:
        print(f"✅ Current Replit Domain: {replit_domain}")
    else:
        print("⚠️ No Replit domain found in environment")
    
    # Check required environment variables
    required_vars = [
        'DATABASE_URL',
        'SESSION_SECRET',
        'FLASK_ENV'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in Replit Secrets:")
        for var in missing_vars:
            print(f"  - {var}")
    else:
        print("✅ All required environment variables are set")
    
    print("\n🚀 Domain Configuration Complete!")
    print("Your app will be accessible at: https://<your-repl-name>.<username>.repl.co")
    print("The domain will be automatically assigned by Replit when you run your app.")
    print("Use the 'Open in new tab' button in the Replit webview to get the correct URL.")

if __name__ == "__main__":
    setup_replit_domain()
