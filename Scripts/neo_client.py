import logging
import os

# Critical: Preload libraries before any pandas/numpy operations
import ctypes
try:
    # Direct library loading to ensure availability
    ctypes.CDLL('/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib/libstdc++.so.6')
    ctypes.CDLL('/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib/libz.so.1')
except Exception as e:
    print(f"Library preload warning in neo_client: {e}")

class NeoClient:
    
    def initialize_client_with_tokens(self, access_token, session_token, sid):
        """Initialize Neo client with existing tokens"""
        try:
            from neo_api_client import NeoAPI
            
            client = NeoAPI(
                consumer_key=os.environ.get('KOTAK_CONSUMER_KEY'),
                consumer_secret=os.environ.get('KOTAK_CONSUMER_SECRET'),
                environment='prod'
            )
            
            # Set tokens directly
            client.access_token = access_token
            client.session_token = session_token
            client.sid = sid
            
            return client
        except Exception as e:
            logging.error(f"Failed to initialize client with tokens: {e}")
            return None
    """Kotak Neo API Client wrapper"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def initialize_neo_client(self, ucc):
        """Initialize the Kotak Neo API client - following Jupyter notebook implementation"""
        try:
            from neo_api_client import NeoAPI
            
            # Get credentials from environment or defaults
            consumer_key = os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa')
            consumer_secret = os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a')
            neo_fin_key = os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi')
            
            # Get base URL - standard Kotak Neo production URL
            base_url = "https://gw-napi.kotaksecurities.com/"
            self.logger.info(f"Base URL retrieved: {base_url}")
            
            # Initialize client exactly like in notebook
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=None,
                neo_fin_key=neo_fin_key
            )
            
            self.logger.info("✅ Neo API client initialized successfully!")
            return client
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing Neo API client: {str(e)}")
            return None
    
    def initialize_client_with_tokens(self, access_token, session_token, sid=None):
        """Initialize the Kotak Neo API client with existing tokens"""
        try:
            from neo_api_client import NeoAPI
            
            # Use credentials from environment
            consumer_key = os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa')
            consumer_secret = os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a')
            neo_fin_key = os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi')
            
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=access_token,
                neo_fin_key=neo_fin_key
            )
            
            # Set the session ID if provided
            if sid:
                client.session_token = sid
                self.logger.info(f"Session ID set: {sid[:10]}...")
            
            self.logger.info("Neo API client initialized with existing tokens")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client with tokens: {str(e)}")
            return None
    
    def validate_session(self, client):
        """Validate if the session is properly authenticated with complete 2FA"""
        try:
            # Try multiple API calls to validate session
            validation_methods = [
                ('limits', lambda: client.limits()),
                ('positions', lambda: client.positions()),
                ('holdings', lambda: client.holdings())
            ]
            
            for method_name, method_call in validation_methods:
                try:
                    response = method_call()
                    self.logger.info(f"Testing {method_name} API: {response}")
                    
                    # Check for successful response
                    if response:
                        # Handle different response structures
                        if isinstance(response, dict):
                            # Check for error in response
                            if 'error' in response:
                                continue  # Try next method
                            
                            # Check for data or success indicators
                            if ('data' in response or 'Data' in response or 
                                'success' in response or len(response) > 0):
                                self.logger.info(f"✅ Session validation successful using {method_name}")
                                return True
                        elif isinstance(response, list):
                            # List response is usually valid
                            self.logger.info(f"✅ Session validation successful using {method_name} (list response)")
                            return True
                        elif response is not None:
                            # Any non-None response indicates working session
                            self.logger.info(f"✅ Session validation successful using {method_name} (non-null response)")
                            return True
                except Exception as method_error:
                    self.logger.debug(f"Method {method_name} failed: {str(method_error)}")
                    continue
            
            self.logger.warning("⚠️ All validation methods failed")
            return False
            
        except Exception as e:
            error_msg = str(e)
            if any(phrase in error_msg for phrase in [
                "Complete the 2fa process", 
                "Invalid Credentials", 
                "Invalid JWT token",
                "2fa process",
                "authentication"
            ]):
                self.logger.error(f"❌ Session validation failed - 2FA required: {error_msg}")
                return False
            else:
                self.logger.warning(f"⚠️ Session validation warning: {error_msg}")
                return False
    
    def login_with_totp(self, client, mobile_number, ucc, totp, mpin):
        """Login using TOTP (Time-based One-Time Password) - following notebook implementation"""
        try:
            self.logger.info("🔐 Attempting TOTP login...")
            
            # Step 1: TOTP Login - following notebook method
            try:
                totp_response = client.login(
                    mobilenumber=mobile_number,
                    password=totp
                )
                self.logger.info("✅ TOTP login successful!")
                self.logger.info(f"Login Response: {totp_response}")
            except Exception as login_error:
                self.logger.error(f"❌ TOTP login step failed: {str(login_error)}")
                return {'success': False, 'message': f'TOTP login failed. Please check your mobile number and TOTP code: {str(login_error)}'}
            
            # Step 2: TOTP Validation - following notebook method
            try:
                validation_response = client.session_2fa(OTP=mpin)
                self.logger.info("✅ TOTP validation successful!")
                self.logger.info(f"Validation Response: {validation_response}")
            except Exception as validation_error:
                self.logger.error(f"❌ TOTP validation step failed: {str(validation_error)}")
                return {'success': False, 'message': f'MPIN validation failed. Please check your MPIN: {str(validation_error)}'}
            
            # Check if validation response contains proper data
            if not validation_response or 'data' not in validation_response:
                return {'success': False, 'message': 'Invalid response from authentication server'}
            
            return {
                'success': True,
                'login_response': totp_response,
                'validation_response': validation_response,
                'client': client
            }
            
        except Exception as e:
            self.logger.error(f"❌ TOTP Login failed: {str(e)}")
            return {'success': False, 'message': f'TOTP Login failed: {str(e)}'}

    def execute_totp_login(self, mobile_number, ucc, totp, mpin):
        """Execute complete TOTP login process - following notebook flow"""
        try:
            self.logger.info("🔐 Starting TOTP login process...")
            
            # Step 1: Initialize Neo API client
            client = self.initialize_neo_client(ucc)
            if not client:
                return {'success': False, 'message': 'Failed to initialize Neo API client'}
            
            # Step 2: Execute TOTP login
            login_result = self.login_with_totp(client, mobile_number, ucc, totp, mpin)
            
            if login_result['success']:
                self.logger.info("🎉 Login completed successfully!")
                
                # Extract complete session data from validation response
                validation_data = login_result['validation_response'].get('data', {})
                
                # Prepare complete session data with all available fields
                complete_session_data = validation_data.copy()
                complete_session_data.update({
                    'access_token': validation_data.get('token'),
                    'session_token': validation_data.get('token'),
                    'sid': validation_data.get('sid'),
                    'rid': validation_data.get('rid'),
                    'ucc': validation_data.get('ucc'),
                    'greeting_name': validation_data.get('greetingName'),
                    'is_trial_account': validation_data.get('isTrialAccount'),
                    'user_id': validation_data.get('userId'),
                    'client_code': validation_data.get('clientCode'),
                    'product_code': validation_data.get('productCode'),
                    'account_type': validation_data.get('accountType'),
                    'branch_code': validation_data.get('branchCode'),
                    'exchange_codes': validation_data.get('exchangeCodes'),
                    'order_types': validation_data.get('orderTypes'),
                    'product_types': validation_data.get('productTypes'),
                    'token_type': validation_data.get('token_type'),
                    'scope': validation_data.get('scope'),
                    'expires_in': validation_data.get('expires_in')
                })
                
                return {
                    'success': True,
                    'client': client,
                    'session_data': complete_session_data,
                    'access_token': validation_data.get('token'),
                    'session_token': validation_data.get('token'),
                    'sid': validation_data.get('sid'),
                    'ucc': validation_data.get('ucc'),
                    'greeting_name': validation_data.get('greetingName')
                }
            else:
                return login_result
                
        except Exception as e:
            self.logger.error(f"❌ TOTP Login process failed: {str(e)}")
            return {'success': False, 'message': f'TOTP Login failed: {str(e)}'}

    def initialize_client(self, credentials):
        """Initialize the Kotak Neo API client"""
        try:
            # Check if tokens are provided in credentials
            if 'access_token' in credentials and credentials['access_token']:
                return self.initialize_client_with_tokens(
                    credentials['access_token'],
                    credentials.get('session_token'),
                    credentials.get('sid')
                )
            
            # Fallback to traditional initialization
            consumer_key = credentials.get('consumer_key', os.environ.get('KOTAK_CONSUMER_KEY', '4OKP7bOfI5ozzCB1EI4a6DOIyJsa'))
            consumer_secret = credentials.get('consumer_secret', os.environ.get('KOTAK_CONSUMER_SECRET', 'cnLm3ZSJVLCOPiwTk4xAJw5G8v0a'))
            neo_fin_key = credentials.get('neo_fin_key', os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi'))
            
            client = NeoAPI(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                environment='prod',
                access_token=None,
                neo_fin_key=neo_fin_key
            )
            
            self.logger.info("Neo API client initialized successfully!")
            return client
            
        except Exception as e:
            self.logger.error(f"Error initializing Neo API client: {str(e)}")
            return None