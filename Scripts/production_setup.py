#!/usr/bin/env python3
"""
Production Setup Script for Kotak Neo Trading Platform
Automates deployment preparation and verification
"""

import os
import sys
import json
import subprocess
import secrets
from pathlib import Path

class ProductionSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.required_files = [
            'render.yaml',
            'render_requirements.txt', 
            'main_render.py',
            'Procfile',
            'runtime.txt'
        ]
        
    def generate_session_secret(self):
        """Generate secure session secret"""
        return secrets.token_urlsafe(32)
    
    def verify_requirements(self):
        """Verify all deployment files exist"""
        print("🔍 Verifying deployment files...")
        missing_files = []
        
        for file in self.required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        
        print("✅ All deployment files present")
        return True
    
    def create_env_template(self):
        """Create environment variables template"""
        env_template = {
            "DATABASE_URL": "postgresql://user:password@host:5432/database",
            "SESSION_SECRET": self.generate_session_secret(),
            "ENVIRONMENT": "production",
            "FLASK_ENV": "production",
            "DEMO_MODE": "false"
        }
        
        # Write to .env.example
        with open('.env.example', 'w') as f:
            for key, value in env_template.items():
                f.write(f"{key}={value}\n")
        
        print("✅ Created .env.example template")
        return env_template
    
    def validate_app_structure(self):
        """Validate Flask application structure"""
        print("🔍 Validating application structure...")
        
        required_modules = ['app.py', 'models.py', 'templates/', 'static/']
        missing = []
        
        for module in required_modules:
            if not (self.project_root / module).exists():
                missing.append(module)
        
        if missing:
            print(f"❌ Missing application files: {', '.join(missing)}")
            return False
        
        print("✅ Application structure valid")
        return True
    
    def test_imports(self):
        """Test critical imports"""
        print("🔍 Testing imports...")
        
        try:
            # Test main app import
            sys.path.insert(0, str(self.project_root))
            from app import app, db
            print("✅ Flask app imports successful")
            
            # Test models
            import scripts.models as models
            import scripts.models_etf as models_etf
            print("✅ Model imports successful")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
    
    def create_deployment_checklist(self):
        """Create deployment checklist"""
        checklist = """
# Render Deployment Checklist

## Pre-Deployment
- [ ] All deployment files present
- [ ] Dependencies in render_requirements.txt
- [ ] Environment variables configured
- [ ] Database schema validated
- [ ] Application imports working

## Render Configuration
- [ ] GitHub repository connected
- [ ] PostgreSQL database created
- [ ] Web service configured
- [ ] Environment variables set
- [ ] Health check endpoint working

## Post-Deployment
- [ ] Application accessible
- [ ] Database tables created
- [ ] Login functionality working
- [ ] ETF signals displaying
- [ ] Health checks passing
- [ ] SSL certificate active

## Production Monitoring
- [ ] Logs accessible
- [ ] Performance metrics
- [ ] Error monitoring
- [ ] Backup strategy

Generated SESSION_SECRET: {secret}
""".format(secret=self.generate_session_secret())

        with open('DEPLOYMENT_CHECKLIST.md', 'w') as f:
            f.write(checklist)
        
        print("✅ Created deployment checklist")
    
    def run_setup(self):
        """Run complete production setup"""
        print("🚀 Starting Production Setup for Kotak Neo Trading Platform\n")
        
        # Verify deployment files
        if not self.verify_requirements():
            print("❌ Setup failed: Missing deployment files")
            return False
        
        # Validate application structure
        if not self.validate_app_structure():
            print("❌ Setup failed: Invalid application structure")
            return False
        
        # Test imports
        if not self.test_imports():
            print("❌ Setup failed: Import errors")
            return False
        
        # Create environment template
        env_vars = self.create_env_template()
        
        # Create deployment checklist
        self.create_deployment_checklist()
        
        print("\n✅ Production setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Push code to GitHub repository")
        print("2. Create Render account at https://render.com")
        print("3. Deploy using Blueprint (render.yaml)")
        print("4. Set environment variables in Render dashboard")
        print("5. Verify deployment using health checks")
        
        print(f"\n🔑 Generated SESSION_SECRET: {env_vars['SESSION_SECRET']}")
        print("💡 Save this secret key for Render environment variables")
        
        return True

if __name__ == "__main__":
    setup = ProductionSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)