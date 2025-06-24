"""
Notifications API endpoints
"""
from flask import Blueprint, request, jsonify, session
from models import db, User
from models_etf import UserNotification, AdminTradeSignal
from datetime import datetime
import logging

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api')

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get user notifications"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        notifications = UserNotification.query.filter_by(user_id=session['user_id']).order_by(UserNotification.created_at.desc()).limit(50).all()
        unread_count = UserNotification.query.filter_by(user_id=session['user_id'], is_read=False).count()
        
        return jsonify({
            'success': True,
            'notifications': [notification.to_dict() for notification in notifications],
            'unread_count': unread_count
        })
        
    except Exception as e:
        logging.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching notifications: {str(e)}'}), 500

@notifications_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        notification = UserNotification.query.filter_by(id=notification_id, user_id=session['user_id']).first()
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating notification: {str(e)}'}), 500

@notifications_bp.route('/received-signals', methods=['GET'])
def get_received_signals():
    """Get trade signals received by current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        signals = AdminTradeSignal.query.filter_by(target_user_id=session['user_id']).order_by(AdminTradeSignal.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'signals': [signal.to_dict() for signal in signals]
        })
        
    except Exception as e:
        logging.error(f"Error fetching received signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching signals: {str(e)}'}), 500

@notifications_bp.route('/signals/<int:signal_id>/read', methods=['POST'])
def mark_signal_read(signal_id):
    """Mark trade signal as read"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        signal = AdminTradeSignal.query.filter_by(id=signal_id, target_user_id=session['user_id']).first()
        if not signal:
            return jsonify({'success': False, 'message': 'Signal not found'}), 404
        
        signal.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Signal marked as read'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error marking signal as read: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating signal: {str(e)}'}), 500

@notifications_bp.route('/signals/<int:signal_id>/execute', methods=['POST'])
def execute_signal(signal_id):
    """Mark trade signal as executed"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        signal = AdminTradeSignal.query.filter_by(id=signal_id, target_user_id=session['user_id']).first()
        if not signal:
            return jsonify({'success': False, 'message': 'Signal not found'}), 404
        
        signal.is_executed = True
        signal.is_read = True
        
        # Create a notification for the admin who sent the signal
        admin_notification = UserNotification(
            user_id=signal.admin_user_id,
            title=f"Signal Executed: {signal.signal_title}",
            message=f"User has executed your trade signal for {signal.symbol}",
            notification_type='INFO',
            priority='MEDIUM',
            related_signal_id=signal.id
        )
        
        db.session.add(admin_notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Signal marked as executed'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error executing signal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error executing signal: {str(e)}'}), 500

@notifications_bp.route('/user/admin-status', methods=['GET'])
def check_admin_status():
    """Check if current user has admin privileges"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # For now, consider all users as potential admins
        # You can add proper role-based access control later
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Simple admin check - you can enhance this with proper roles
        is_admin = True  # For now, all users can send signals
        
        return jsonify({
            'success': True,
            'is_admin': is_admin,
            'user_id': user.id
        })
        
    except Exception as e:
        logging.error(f"Error checking admin status: {str(e)}")
        return jsonify({'success': False, 'message': f'Error checking admin status: {str(e)}'}), 500