from flask import Blueprint, request, jsonify
from app.services.firebase_config import db

calendar_bp = Blueprint("calendar_bp", __name__)

@calendar_bp.route("/apply", methods=["POST"])
def apply_for_company():
    """
    When user applies to a company:
    1. Store application in Firestore
    2. Auto-create calendar event for that application
    """
    try:
        data = request.json
        user_id = data.get("userId")
        company_name = data.get("company")
        date = data.get("date", "2025-09-30")   # default for now
        time = data.get("time", "10:00 AM")

        if not user_id or not company_name:
            return jsonify({"error": "Missing userId or company"}), 400

        # Step 1: Save application
        db.collection("applications").add({
            "userId": user_id,
            "company": company_name,
            "status": "applied"
        })

        # Step 2: Auto-create calendar event
        event_data = {
            "title": f"Applied to {company_name}",
            "date": date,
            "time": time,
            "description": f"Application submitted for {company_name}",
            "userId": user_id
        }
        db.collection("events").add(event_data)

        return jsonify({
            "success": True,
            "message": f"Application for {company_name} submitted & event created"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calendar_bp.route("/events/<user_id>", methods=["GET"])
def get_user_events(user_id):
    """
    Fetch all calendar events for a specific user
    """
    try:
        events_ref = db.collection("events").where("userId", "==", user_id).stream()
        events = [e.to_dict() for e in events_ref]
        return jsonify(events), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
