
class SessionHelper:
    """Helper class to easily access stored session data"""
    
    def __init__(self):
        from scripts.session_manager import SessionManager
        self.session_manager = SessionManager()
    
    def get_current_user_data(self):
        """Get complete current user session data"""
        return self.session_manager.get_session('default_user')
    
    def get_access_token(self):
        """Get current access token"""
        return self.session_manager.get_session_field('default_user', 'access_token')
    
    def get_session_token(self):
        """Get current session token"""
        return self.session_manager.get_session_field('default_user', 'session_token')
    
    def get_sid(self):
        """Get current SID"""
        return self.session_manager.get_session_field('default_user', 'sid')
    
    def get_rid(self):
        """Get current RID"""
        return self.session_manager.get_session_field('default_user', 'rid')
    
    def get_ucc(self):
        """Get current UCC"""
        return self.session_manager.get_session_field('default_user', 'ucc')
    
    def get_greeting_name(self):
        """Get current greeting name"""
        return self.session_manager.get_session_field('default_user', 'greeting_name')
    
    def is_trial_account(self):
        """Check if current account is trial"""
        return self.session_manager.get_session_field('default_user', 'is_trial_account')
    
    def get_user_id(self):
        """Get current user ID"""
        return self.session_manager.get_session_field('default_user', 'user_id')
    
    def get_client_code(self):
        """Get current client code"""
        return self.session_manager.get_session_field('default_user', 'client_code')
    
    def get_product_code(self):
        """Get current product code"""
        return self.session_manager.get_session_field('default_user', 'product_code')
    
    def get_account_type(self):
        """Get current account type"""
        return self.session_manager.get_session_field('default_user', 'account_type')
    
    def get_branch_code(self):
        """Get current branch code"""
        return self.session_manager.get_session_field('default_user', 'branch_code')
    
    def get_exchange_codes(self):
        """Get available exchange codes"""
        return self.session_manager.get_session_field('default_user', 'exchange_codes') or []
    
    def get_order_types(self):
        """Get available order types"""
        return self.session_manager.get_session_field('default_user', 'order_types') or []
    
    def get_product_types(self):
        """Get available product types"""
        return self.session_manager.get_session_field('default_user', 'product_types') or []
    
    def get_full_login_response(self):
        """Get complete original login response"""
        return self.session_manager.get_full_response('default_user')
    
    def print_all_session_data(self):
        """Print all stored session data for debugging"""
        session_data = self.get_current_user_data()
        if session_data:
            print("=== COMPLETE SESSION DATA ===")
            for key, value in session_data.items():
                if key == 'full_response':
                    print(f"{key}: [Complete Response Object]")
                elif key in ['access_token', 'session_token'] and value:
                    print(f"{key}: {value[:20]}...")
                else:
                    print(f"{key}: {value}")
        else:
            print("No session data found")

# Usage examples:
if __name__ == "__main__":
    helper = SessionHelper()
    
    # Get individual fields
    print(f"UCC: {helper.get_ucc()}")
    print(f"Greeting Name: {helper.get_greeting_name()}")
    print(f"Is Trial Account: {helper.is_trial_account()}")
    print(f"User ID: {helper.get_user_id()}")
    print(f"Client Code: {helper.get_client_code()}")
    
    # Print all data
    helper.print_all_session_data()
