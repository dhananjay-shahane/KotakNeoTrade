"""
Authentication API - Handles user login, logout, and session management
Contains login business logic moved from app.py for better modularity
"""

import logging
from datetime import datetime, timedelta
from flask import request, session, flash, render_template, redirect, url_for


def handle_login_post(neo_client, user_manager):
    """
    Handle POST request for login with TOTP authentication
    Returns: (success_redirect, template_response) tuple
    """
    try:
        # Get form data
        mobile_number = request.form.get('mobile_number', '').strip()
        ucc = request.form.get('ucc', '').strip()
        totp = request.form.get('totp', '').strip()
        mpin = request.form.get('mpin', '').strip()

        # Validate inputs
        if not all([mobile_number, ucc, totp, mpin]):
            flash('All fields are required', 'error')
            return None, render_template('login.html')

        # Validate formats
        if len(mobile_number) != 10 or not mobile_number.isdigit():
            flash('Mobile number must be 10 digits', 'error')
            return None, render_template('login.html')

        if len(totp) != 6 or not totp.isdigit():
            flash('TOTP must be 6 digits', 'error')
            return None, render_template('login.html')

        if len(mpin) != 6 or not mpin.isdigit():
            flash('MPIN must be 6 digits', 'error')
            return None, render_template('login.html')

        # Execute TOTP login
        result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)

        if result and result.get('success'):
            client = result.get('client')
            session_data = result.get('session_data', {})

            # Store in session
            session['authenticated'] = True
            session['access_token'] = session_data.get('access_token')
            session['session_token'] = session_data.get('session_token')
            session['sid'] = session_data.get('sid')
            session['ucc'] = ucc
            session['client'] = client
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session['greeting_name'] = session_data.get('greetingName', ucc)
            session.permanent = True

            # Set session expiration (24 hours from now)
            expiry_time = datetime.now() + timedelta(hours=24)
            session['session_expires_at'] = expiry_time.isoformat()

            # Store additional user data
            session['rid'] = session_data.get('rid')
            session['user_id'] = session_data.get('user_id')
            session['client_code'] = session_data.get('client_code')
            session['is_trial_account'] = session_data.get('is_trial_account')

            # Store user data in database
            try:
                login_response = {
                    'success': True,
                    'data': {
                        'ucc': ucc,
                        'mobile_number': mobile_number,
                        'greeting_name': session_data.get('greetingName'),
                        'user_id': session_data.get('user_id'),
                        'client_code': session_data.get('client_code'),
                        'product_code': session_data.get('product_code'),
                        'account_type': session_data.get('account_type'),
                        'branch_code': session_data.get('branch_code'),
                        'is_trial_account': session_data.get('is_trial_account', False),
                        'access_token': session_data.get('access_token'),
                        'session_token': session_data.get('session_token'),
                        'sid': session_data.get('sid'),
                        'rid': session_data.get('rid')
                    }
                }

                db_user = user_manager.create_or_update_user(login_response)
                user_session = user_manager.create_user_session(db_user.id, login_response)

                session['db_user_id'] = db_user.id
                session['db_session_id'] = user_session.session_id

                logging.info(f"User data stored in database for UCC: {ucc}")

            except Exception as db_error:
                logging.error(f"Failed to store user data in database: {db_error}")

            flash('Successfully authenticated with TOTP!', 'success')
            return redirect(url_for('dashboard')), None
        else:
            error_msg = result.get('message', 'Authentication failed') if result else 'Login failed'
            flash(f'TOTP login failed: {error_msg}', 'error')

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash(f'Login failed: {str(e)}', 'error')

    return None, render_template('login.html')


def handle_login_get():
    """
    Handle GET request for login page
    Returns: template response
    """
    # Check if session expired and show message
    session_expired = request.args.get('expired') == 'true'
    if session_expired:
        flash('Your session has expired. Please login again.', 'warning')
    
    return render_template('login.html')


def handle_logout():
    """
    Handle user logout and session cleanup
    Returns: redirect response
    """
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))