"""
Notification Routes - API endpoints for notification management
"""
from flask import Blueprint, request, jsonify
from app.services.firebase_service import get_db, token_required
from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/check-deadlines", methods=["POST"])
@token_required
def check_deadline_notifications():
    """
    Check and generate deadline notifications for the current user.
    This can be called periodically or manually.
    """
    try:
        uid = request.user["uid"]
        db = get_db()
        notification_service = NotificationService(db)
        
        count = notification_service.check_and_update_deadline_notifications(uid)
        
        return jsonify({
            "message": f"Checked deadline notifications",
            "notifications_created": count
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notifications_bp.route("/mark-read/<notification_id>", methods=["PUT"])
@token_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        uid = request.user["uid"]
        db = get_db()
        
        notification_ref = db.collection('notifications').document(notification_id)
        notification_doc = notification_ref.get()
        
        if not notification_doc.exists:
            return jsonify({"error": "Notification not found"}), 404
        
        notification_data = notification_doc.to_dict()
        if notification_data.get('userId') != uid:
            return jsonify({"error": "Unauthorized"}), 403
        
        notification_ref.update({'isRead': True})
        
        return jsonify({"message": "Notification marked as read"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notifications_bp.route("/mark-all-read", methods=["PUT"])
@token_required
def mark_all_notifications_read():
    """Mark all notifications as read for the current user."""
    try:
        uid = request.user["uid"]
        db = get_db()
        
        notifications = db.collection('notifications').where(
            'userId', '==', uid
        ).where('isRead', '==', False).get()
        
        batch = db.batch()
        for notification in notifications:
            batch.update(notification.reference, {'isRead': True})
        
        batch.commit()
        
        return jsonify({
            "message": "All notifications marked as read",
            "count": len(notifications)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

