"""
Authentication routes for the trading platform
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Simple demo login
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            session['user_logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('portfolio'))
        else:
            flash('Please enter both username and password', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if username and email and password:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Please fill in all fields', 'error')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('portfolio'))