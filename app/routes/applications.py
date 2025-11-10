# from flask import Blueprint, request, jsonify
# from app.services.firebase_service import get_db
# from firebase_admin import firestore

# applications_bp = Blueprint('applications_bp', __name__)

# @applications_bp.route('/', methods=['GET'])
# def get_applications():
#     try:
#         db = get_db()
#         apps_ref = db.collection("applications")
#         docs = apps_ref.get()
#         applications = [doc.to_dict() for doc in docs]
#         return jsonify({"applications": applications}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @applications_bp.route('/', methods=['POST'])
# def create_application():
#     data = request.get_json()
#     if not data or not data.get("user_id") or not data.get("company_id"):
#         return jsonify({"error": "Missing user_id or company_id"}), 400

#     try:
#         db = get_db()
#         doc_ref = db.collection("applications").document()
#         doc_ref.set({
#             "user_id": data.get("user_id"),
#             "company_id": data.get("company_id"),
#             "status": data.get("status", "pending"),
#             "applied_at": firestore.SERVER_TIMESTAMP
#         })
#         return jsonify({"message": "Application created successfully", "id": doc_ref.id}), 201
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, request, jsonify
from app.services.firebase_service import get_db, verify_user_token
from app.services.notification_service import NotificationService
from datetime import datetime
import uuid

applications_bp = Blueprint("applications", __name__)

# Create application
@applications_bp.route("/", methods=["POST"])
def create_application():
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        token = auth_header.split(" ")[1]
        decoded_token = verify_user_token(token)
        user_id = decoded_token["uid"]

        data = request.get_json()
        if not data or "company_id" not in data:
            return jsonify({"error": "company_id is required"}), 400

        db = get_db()
        applications_ref = db.collection("applications")
        app_id = str(uuid.uuid4())
        
        # Get company name if provided, otherwise fetch from companies collection
        company_name = data.get("company_name") or data.get("companyName")
        if not company_name and data.get("company_id"):
            try:
                company_doc = db.collection("companies").document(data["company_id"]).get()
                if company_doc.exists:
                    company_data = company_doc.to_dict()
                    company_name = company_data.get("company_name") or company_data.get("name")
            except:
                pass

        application = {
            "id": app_id,
            "userId": user_id,
            "user_id": user_id,  # Keep both for compatibility
            "companyId": data["company_id"],
            "company_id": data["company_id"],  # Keep both for compatibility
            "companyName": company_name,
            "company_name": company_name,  # Keep both for compatibility
            "status": "applied",
            "appliedAt": datetime.utcnow().isoformat(),
            "applied_at": datetime.utcnow().isoformat(),  # Keep both for compatibility
            "deadline": data.get("deadline"),        # optional
            "interview_date": data.get("interview_date") or data.get("interviewDate"),  # optional
        }

        applications_ref.document(app_id).set(application)
        
        # Generate notifications for this application
        notification_service = NotificationService(db)
        notification_ids = notification_service.generate_application_notifications(application)
        
        return jsonify({
            "message": "Application created",
            "id": app_id,
            "notifications_created": len(notification_ids)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get all applications for logged-in user
@applications_bp.route("/", methods=["GET"])
def get_applications():
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        token = auth_header.split(" ")[1]
        decoded_token = verify_user_token(token)
        user_id = decoded_token["uid"]

        db = get_db()
        applications_ref = db.collection("applications").where("user_id", "==", user_id)
        docs = applications_ref.stream()

        applications = [doc.to_dict() for doc in docs]
        return jsonify(applications), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get single application
@applications_bp.route("/<app_id>", methods=["GET"])
def get_application(app_id):
    try:
        db = get_db()
        app_ref = db.collection("applications").document(app_id)
        doc = app_ref.get()
        if not doc.exists:
            return jsonify({"error": "Application not found"}), 404
        return jsonify(doc.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Update application (status, interview_date, etc.)
@applications_bp.route("/<app_id>", methods=["PUT"])
def update_application(app_id):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        token = auth_header.split(" ")[1]
        decoded_token = verify_user_token(token)
        user_id = decoded_token["uid"]
        
        data = request.get_json()
        db = get_db()
        app_ref = db.collection("applications").document(app_id)
        doc = app_ref.get()
        if not doc.exists:
            return jsonify({"error": "Application not found"}), 404

        app_data = doc.to_dict()
        if app_data.get("userId") != user_id and app_data.get("user_id") != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        old_status = app_data.get("status")
        new_status = data.get("status")
        
        # Update application
        app_ref.update(data)
        
        # Generate notification if status changed
        if new_status and new_status != old_status:
            notification_service = NotificationService(db)
            company_name = app_data.get("companyName") or app_data.get("company_name")
            notification_service.create_status_update_notification(
                user_id=user_id,
                company_name=company_name or "Company",
                old_status=old_status or "pending",
                new_status=new_status,
                application_id=app_id
            )
        
        # Generate interview notification if interview date is added/updated
        if data.get("interview_date") or data.get("interviewDate"):
            notification_service = NotificationService(db)
            company_name = app_data.get("companyName") or app_data.get("company_name")
            interview_date = data.get("interview_date") or data.get("interviewDate")
            notification_service._create_interview_notification(
                user_id=user_id,
                company_name=company_name or "Company",
                interview_date=interview_date,
                application_id=app_id
            )
        
        return jsonify({"message": "Application updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete application
@applications_bp.route("/<app_id>", methods=["DELETE"])
def delete_application(app_id):
    try:
        db = get_db()
        app_ref = db.collection("applications").document(app_id)
        app_ref.delete()
        return jsonify({"message": "Application deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
