"""
Kotak Neo API Blueprint
Handles Kotak Neo authentication and trading operations
"""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from kotak_auth_service import KotakAuthService
from kotak_models import KotakAccount, TradingSession, db

# Create blueprint
kotak_api = Blueprint('kotak_api', __name__, url_prefix='/kotak')

# Initialize auth service
auth_service = KotakAuthService()

@kotak_api.route('/login', methods=['GET', 'POST'])
@login_required
def kotak_login():
    """Kotak Neo login page and authentication"""
    if request.method == 'POST':
        try:
            # Get form data
            mobile_number = request.form.get('mobile_number', '').strip()
            ucc = request.form.get('ucc', '').strip()
            mpin = request.form.get('mpin', '').strip()
            totp_code = request.form.get('totp_code', '').strip()
            
            # Authenticate with Kotak Neo
            auth_result = auth_service.authenticate_user(
                mobile_number=mobile_number,
                ucc=ucc,
                mpin=mpin,
                totp_code=totp_code
            )
            
            if auth_result['success']:
                # Store session data
                session['kotak_authenticated'] = True
                session['kotak_ucc'] = ucc
                session['kotak_mobile'] = mobile_number
                
                flash('Successfully logged in to Kotak Neo!', 'success')
                return redirect(url_for('kotak_api.dashboard'))
            else:
                flash(f'Login failed: {auth_result["error"]}', 'error')
                
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('login.html')

@kotak_api.route('/dashboard')
@login_required
def dashboard():
    """Kotak Neo dashboard"""
    if not session.get('kotak_authenticated'):
        flash('Please log in to Kotak Neo first', 'warning')
        return redirect(url_for('kotak_api.kotak_login'))
    
    # Get account info
    ucc = session.get('kotak_ucc')
    mobile = session.get('kotak_mobile')
    
    return render_template('kotak_dashboard.html', ucc=ucc, mobile=mobile)

@kotak_api.route('/logout')
@login_required
def logout():
    """Logout from Kotak Neo"""
    # Clear Kotak session data
    session.pop('kotak_authenticated', None)
    session.pop('kotak_ucc', None)
    session.pop('kotak_mobile', None)
    
    flash('Logged out from Kotak Neo', 'info')
    return redirect(url_for('portfolio'))

@kotak_api.route('/orders')
@login_required
def orders():
    """Orders page"""
    if not session.get('kotak_authenticated'):
        flash('Please log in to Kotak Neo first', 'warning')
        return redirect(url_for('kotak_api.kotak_login'))
    
    return render_template('kotak_orders.html')

@kotak_api.route('/positions')
@login_required
def positions():
    """Positions page"""
    if not session.get('kotak_authenticated'):
        flash('Please log in to Kotak Neo first', 'warning')
        return redirect(url_for('kotak_api.kotak_login'))
    
    return render_template('kotak_positions.html')

@kotak_api.route('/holdings')
@login_required
def holdings():
    """Holdings page"""
    if not session.get('kotak_authenticated'):
        flash('Please log in to Kotak Neo first', 'warning')
        return redirect(url_for('kotak_api.kotak_login'))
    
    return render_template('kotak_holdings.html')

# API endpoints
@kotak_api.route('/api/authenticate', methods=['POST'])
def api_authenticate():
    """API endpoint for Kotak authentication"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Authenticate with Kotak Neo
        auth_result = auth_service.authenticate_user(
            mobile_number=data.get('mobile_number'),
            ucc=data.get('ucc'),
            mpin=data.get('mpin'),
            totp_code=data.get('totp_code')
        )
        
        if auth_result['success']:
            # Store session data
            session['kotak_authenticated'] = True
            session['kotak_ucc'] = data.get('ucc')
            session['kotak_mobile'] = data.get('mobile_number')
        
        return jsonify(auth_result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@kotak_api.route('/api/status')
@login_required
def api_status():
    """Get Kotak authentication status"""
    try:
        status = {
            'authenticated': session.get('kotak_authenticated', False),
            'ucc': session.get('kotak_ucc'),
            'mobile': session.get('kotak_mobile')
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@kotak_api.route('/api/account-info')
@login_required
def api_account_info():
    """Get account information"""
    try:
        if not session.get('kotak_authenticated'):
            return jsonify({'error': 'Not authenticated with Kotak Neo'}), 401
        
        # Get account info from database
        kotak_account = KotakAccount.query.filter_by(
            user_id=current_user.id,
            ucc=session.get('kotak_ucc')
        ).first()
        
        if kotak_account:
            return jsonify(kotak_account.to_dict())
        else:
            return jsonify({'error': 'Account not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500