"""
Kotak Neo API endpoints for authentication and account management
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

def get_user_orders(user_id):
    """Get real orders data from Kotak Neo API or database"""
    try:
        # Connect to Kotak Neo API session for this user
        from kotak_models import KotakAccount, TradingSession
        account = KotakAccount.query.filter_by(user_id=user_id, is_active=True).first()

        if not account:
            return {'success': False, 'message': 'No active Kotak account found'}

        # Get orders from actual API or database
        session = TradingSession.query.filter_by(account_id=account.id, is_active=True).first()
        if session and session.access_token:
            # Use real Kotak Neo API to fetch orders
            from kotak_neo_project.Scripts.trading_functions import TradingFunctions
            trading_functions = TradingFunctions()
            orders = trading_functions.get_orders(session.client_data)
            return {'success': True, 'orders': orders}
        else:
            return {'success': False, 'message': 'No active trading session'}

    except Exception as e:
        return {'success': False, 'message': str(e)}

def get_user_positions(user_id):
    """Get real positions data from Kotak Neo API or database"""
    try:
        from kotak_models import KotakAccount, TradingSession
        account = KotakAccount.query.filter_by(user_id=user_id, is_active=True).first()

        if not account:
            return {'success': False, 'message': 'No active Kotak account found'}

        session = TradingSession.query.filter_by(account_id=account.id, is_active=True).first()
        if session and session.access_token:
            from kotak_neo_project.Scripts.trading_functions import TradingFunctions
            trading_functions = TradingFunctions()
            positions_data = trading_functions.get_positions(session.client_data)
            return {'success': True, 'positions': positions_data.get('positions', []), 'summary': positions_data.get('summary', {})}
        else:
            return {'success': False, 'message': 'No active trading session'}

    except Exception as e:
        return {'success': False, 'message': str(e)}

def get_user_holdings(user_id):
    """Get real holdings data from Kotak Neo API or database"""
    try:
        from kotak_models import KotakAccount, TradingSession
        account = KotakAccount.query.filter_by(user_id=user_id, is_active=True).first()

        if not account:
            return {'success': False, 'message': 'No active Kotak account found'}

        session = TradingSession.query.filter_by(account_id=account.id, is_active=True).first()
        if session and session.access_token:
            from kotak_neo_project.Scripts.trading_functions import TradingFunctions
            trading_functions = TradingFunctions()
            holdings_data = trading_functions.get_holdings(session.client_data)
            return {'success': True, 'holdings': holdings_data.get('holdings', []), 'summary': holdings_data.get('summary', {})}
        else:
            return {'success': False, 'message': 'No active trading session'}

    except Exception as e:
        return {'success': False, 'message': str(e)}

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
from kotak_models import db, KotakAccount, TradingSession
from kotak_auth_service import KotakAuthService

kotak_api = Blueprint('kotak_api', __name__)
auth_service = KotakAuthService()

@kotak_api.route('/api/kotak/login', methods=['POST'])
@login_required
def kotak_login():
    """Handle Kotak Neo login"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Extract credentials
        mobile_number = data.get('mobile_number', '').strip()
        ucc = data.get('ucc', '').strip().upper()
        mpin = data.get('mpin', '').strip()
        totp_code = data.get('totp_code', '').strip()

        # Authenticate with Kotak Neo
        result = auth_service.authenticate_user(
            mobile_number=mobile_number,
            ucc=ucc,
            mpin=mpin,
            totp_code=totp_code
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Successfully logged in to Kotak Neo',
                'account': result['account'],
                'redirect': '/portfolio'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500

@kotak_api.route('/api/kotak/logout/<int:account_id>', methods=['POST'])
@login_required
def kotak_logout(account_id):
    """Handle Kotak Neo logout"""
    try:
        result = auth_service.logout_account(account_id)

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Successfully logged out from Kotak Neo'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Logout failed: {str(e)}'
        }), 500

@kotak_api.route('/api/kotak/accounts', methods=['GET'])
@login_required
def get_kotak_accounts():
    """Get all Kotak accounts for current user"""
    try:
        accounts = auth_service.get_user_accounts()
        return jsonify({
            'success': True,
            'accounts': accounts
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch accounts: {str(e)}'
        }), 500

@kotak_api.route('/api/kotak/account/<int:account_id>/switch', methods=['POST'])
@login_required
def switch_account(account_id):
    """Switch to different Kotak account"""
    try:
        account = KotakAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()

        if not account:
            return jsonify({
                'success': False,
                'error': 'Account not found'
            }), 404

        # Check if session is valid
        if not auth_service.is_session_valid(account_id):
            return jsonify({
                'success': False,
                'error': 'Session expired. Please login again.'
            }), 401

        # Update session
        session['kotak_session'] = {
            'account_id': account.id,
            'ucc': account.ucc,
            'mobile_number': account.mobile_number,
            'session_token': account.session_token,
            'switched_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            'success': True,
            'message': f'Switched to account {account.ucc}',
            'account': account.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to switch account: {str(e)}'
        }), 500

@kotak_api.route('/api/kotak/session/status', methods=['GET'])
@login_required
def get_session_status():
    """Get current Kotak session status"""
    try:
        current_session = auth_service.get_current_session()
        accounts = auth_service.get_user_accounts()

        return jsonify({
            'success': True,
            'session': current_session,
            'accounts': accounts,
            'has_active_session': current_session is not None
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get session status: {str(e)}'
        }), 500

@kotak_api.route('/api/kotak/session/validate', methods=['POST'])
@login_required
def validate_session():
    """Validate current session"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')

        if not account_id:
            return jsonify({
                'success': False,
                'error': 'Account ID required'
            }), 400

        is_valid = auth_service.is_session_valid(account_id)

        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': 'Session is valid' if is_valid else 'Session expired'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Session validation failed: {str(e)}'
        }), 500