from flask import Blueprint, jsonify, request
from app.services.firebase_service import get_db, token_required
from firebase_admin import firestore

calender_bp = Blueprint("calender_bp", __name__)

@calender_bp.route("/events", methods=["GET"])
@token_required
def get_events():
    """Get all calendar events for the authenticated user"""
    try:
        uid = request.user["uid"]
        db = get_db()
        # Use 'events' collection or 'reminders' collection based on your schema
        events_ref = db.collection("events").where("userId", "==", uid).order_by("date").get()
        events = []
        for event_doc in events_ref:
            event_data = event_doc.to_dict()
            event_data["id"] = event_doc.id
            events.append(event_data)
        return jsonify({"events": events}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/reminders", methods=["GET"])
@token_required
def get_reminders():
    """Get all reminders for the authenticated user"""
    try:
        uid = request.user["uid"]
        db = get_db()
        # Use 'reminders' collection
        reminders_ref = db.collection("reminders").where("userId", "==", uid).order_by("reminderTime").get()
        reminders = []
        for reminder_doc in reminders_ref:
            reminder_data = reminder_doc.to_dict()
            reminder_data["id"] = reminder_doc.id
            reminders.append(reminder_data)
        return jsonify({"reminders": reminders}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/events", methods=["POST"])
@token_required
def create_event():
    """Create a new calendar event"""
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        title = data.get("title")
        date = data.get("date")
        time = data.get("time", "")
        description = data.get("description", "")
        company_name = data.get("company_name", "")
        
        if not title or not date:
            return jsonify({"error": "Missing required fields: title, date"}), 400
        
        db = get_db()
        event_data = {
            "userId": uid,
            "title": title,
            "date": date,
            "time": time,
            "description": description,
            "company_name": company_name,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        doc_ref = db.collection("events").document()
        doc_ref.set(event_data)
        
        event_data["id"] = doc_ref.id
        return jsonify({"message": "Event created", "event": event_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/reminders", methods=["POST"])
@token_required
def create_reminder():
    """Create a new reminder"""
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        
        title = data.get("title")
        description = data.get("description", "")
        reminder_time = data.get("reminderTime")
        is_completed = data.get("isCompleted", False)
        
        if not title or not reminder_time:
            return jsonify({"error": "Missing required fields: title, reminderTime"}), 400
        
        db = get_db()
        reminder_data = {
            "userId": uid,
            "title": title,
            "description": description,
            "reminderTime": reminder_time,  # Should be a Firestore timestamp
            "isCompleted": is_completed,
        }
        doc_ref = db.collection("reminders").document()
        doc_ref.set(reminder_data)
        
        reminder_data["id"] = doc_ref.id
        return jsonify({"message": "Reminder created", "reminder": reminder_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/events/<event_id>", methods=["DELETE"])
@token_required
def delete_event(event_id):
    """Delete a calendar event"""
    try:
        uid = request.user["uid"]
        db = get_db()
        event_ref = db.collection("events").document(event_id)
        event_doc = event_ref.get()
        
        if not event_doc.exists:
            return jsonify({"error": "Event not found"}), 404
        
        event_data = event_doc.to_dict()
        if event_data.get("userId") != uid:
            return jsonify({"error": "Unauthorized"}), 403
        
        event_ref.delete()
        return jsonify({"message": "Event deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/reminders/<reminder_id>", methods=["DELETE"])
@token_required
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        uid = request.user["uid"]
        db = get_db()
        reminder_ref = db.collection("reminders").document(reminder_id)
        reminder_doc = reminder_ref.get()
        
        if not reminder_doc.exists:
            return jsonify({"error": "Reminder not found"}), 404
        
        reminder_data = reminder_doc.to_dict()
        if reminder_data.get("userId") != uid:
            return jsonify({"error": "Unauthorized"}), 403
        
        reminder_ref.delete()
        return jsonify({"message": "Reminder deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calender_bp.route("/reminders/<reminder_id>", methods=["PUT"])
@token_required
def update_reminder(reminder_id):
    """Update a reminder (e.g., mark as completed)"""
    try:
        uid = request.user["uid"]
        data = request.get_json() or {}
        db = get_db()
        reminder_ref = db.collection("reminders").document(reminder_id)
        reminder_doc = reminder_ref.get()
        
        if not reminder_doc.exists:
            return jsonify({"error": "Reminder not found"}), 404
        
        reminder_data = reminder_doc.to_dict()
        if reminder_data.get("userId") != uid:
            return jsonify({"error": "Unauthorized"}), 403
        
        reminder_ref.update(data)
        return jsonify({"message": "Reminder updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
