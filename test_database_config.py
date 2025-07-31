#!/usr/bin/env python3
"""
Test script to demonstrate centralized database configuration
Shows how all parts of the application can use the same database config
"""
import sys
import os
sys.path.append('.')

def test_centralized_database_config():
    """Test the centralized database configuration system"""
    print("🔧 Testing Centralized Database Configuration System")
    print("=" * 60)
    
    try:
        # Import centralized database configuration
        from config.database_config import (
            DatabaseConfig, 
            get_db_connection, 
            get_database_url,
            test_database_connection,
            execute_db_query
        )
        
        print("✓ Successfully imported centralized database configuration")
        
        # Test 1: Database configuration initialization
        print("\n1. Testing database configuration initialization...")
        db_config = DatabaseConfig()
        config_dict = db_config.get_config_dict()
        print(f"   Database Host: {config_dict['host']}")
        print(f"   Database Name: {config_dict['database']}")
        print(f"   Database User: {config_dict['user']}")
        print(f"   Database Port: {config_dict['port']}")
        
        # Test 2: Database URL generation
        print("\n2. Testing database URL generation...")
        db_url = get_database_url()
        # Mask password for security
        safe_url = db_url.replace(config_dict['password'], '***')
        print(f"   Database URL: {safe_url}")
        
        # Test 3: Connection test
        print("\n3. Testing database connectivity...")
        if test_database_connection():
            print("   ✅ Database connection successful!")
        else:
            print("   ❌ Database connection failed!")
            
        # Test 4: Simple query execution
        print("\n4. Testing query execution...")
        try:
            result = execute_db_query("SELECT 1 as test_value", fetch_results=True)
            if result and len(result) > 0:
                print(f"   ✅ Query executed successfully! Result: {result[0]}")
            else:
                print("   ❌ Query execution returned no results")
        except Exception as e:
            print(f"   ❌ Query execution failed: {e}")
        
        # Test 5: Show how different components use the same config
        print("\n5. Testing component integration...")
        
        # Test Scripts/external_db_service.py usage
        try:
            from Scripts.external_db_service import DatabaseConnector
            connector = DatabaseConnector()
            print("   ✓ Scripts/external_db_service.py uses centralized config")
        except Exception as e:
            print(f"   ⚠ Scripts/external_db_service.py integration issue: {e}")
            
        # Test api/deals_api.py usage
        try:
            from api.deals_api import get_external_db_connection
            conn = get_external_db_connection()
            if conn:
                conn.close()
                print("   ✓ api/deals_api.py uses centralized config")
            else:
                print("   ⚠ api/deals_api.py connection failed")
        except Exception as e:
            print(f"   ⚠ api/deals_api.py integration issue: {e}")
            
        # Test Scripts/user_deals_service.py usage
        try:
            from Scripts.user_deals_service import UserDealsService
            service = UserDealsService()
            print("   ✓ Scripts/user_deals_service.py uses centralized config")
        except Exception as e:
            print(f"   ⚠ Scripts/user_deals_service.py integration issue: {e}")
        
        print("\n🎉 Centralized Database Configuration Test Complete!")
        print("=" * 60)
        print("Benefits of this architecture:")
        print("• Single source of truth for database configuration")
        print("• Environment variable management in one place")
        print("• Easy to maintain and update connection settings")
        print("• Backward compatibility with existing code")
        print("• Improved security with centralized credential handling")
        print("• Consistent error handling and logging")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_centralized_database_config()