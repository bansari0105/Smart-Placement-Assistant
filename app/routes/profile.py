# from flask import Blueprint, request, jsonify
# from app.services.firebase_service import verify_user_token, db

# profile_bp = Blueprint('profile', __name__)

# @profile_bp.route('/setup', methods=['POST'])
# def setup_profile():
#     """
#     Save or update user profile information in Firestore.
#     Requires Authorization Bearer token.
#     """
#     # 1️⃣ Verify token
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return jsonify({"error": "Missing or invalid token"}), 401

#     id_token = auth_header.split("Bearer ")[1]
#     decoded = verify_user_token(id_token)
#     if not decoded:
#         return jsonify({"error": "Invalid token"}), 401

#     uid = decoded['uid']
#     data = request.get_json()

#     if not data:
#         return jsonify({"error": "Missing profile data"}), 400

#     try:
#         # 2️⃣ Save profile in Firestore
#         db.collection('users').document(uid).set({
#             "name": data.get("name", ""),
#             "department": data.get("department", ""),
#             "graduation_year": data.get("graduation_year"),
#             "skills": data.get("skills", [])
#         }, merge=True)

#         return jsonify({"message": "Profile saved successfully"}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @profile_bp.route('/get', methods=['GET'])
# def get_profile():
#     """
#     Fetch user profile details from Firestore.
#     """
#     # 1️⃣ Verify token
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return jsonify({"error": "Missing or invalid token"}), 401

#     id_token = auth_header.split("Bearer ")[1]
#     decoded = verify_user_token(id_token)
#     if not decoded:
#         return jsonify({"error": "Invalid token"}), 401

#     uid = decoded['uid']

#     try:
#         user_doc = db.collection('users').document(uid).get()
#         if user_doc.exists:
#             return jsonify({"profile": user_doc.to_dict(), "profile_complete": True}), 200
#         else:
#             return jsonify({"profile": {}, "profile_complete": False}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# from flask import Blueprint, request, jsonify
# from app.services.firebase_service import verify_user_token, db

# profile_bp = Blueprint('profile_bp', __name__)

# @profile_bp.route('/setup', methods=['POST'])
# def setup_profile():
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return jsonify({"error": "Missing or invalid token"}), 401

#     id_token = auth_header.split("Bearer ")[1]
#     decoded = verify_user_token(id_token)
#     if not decoded:
#         return jsonify({"error": "Invalid token"}), 401

#     uid = decoded['uid']
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Missing profile data"}), 400

#     try:
#         db.collection('users').document(uid).set({
#             "name": data.get("name", ""),
#             "department": data.get("department", ""),
#             "graduation_year": data.get("graduation_year"),
#             "skills": data.get("skills", [])
#         }, merge=True)
#         return jsonify({"message": "Profile saved successfully"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @profile_bp.route('/get', methods=['GET'])
# def get_profile():
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return jsonify({"error": "Missing or invalid token"}), 401

#     id_token = auth_header.split("Bearer ")[1]
#     decoded = verify_user_token(id_token)
#     if not decoded:
#         return jsonify({"error": "Invalid token"}), 401

#     uid = decoded['uid']

#     try:
#         user_doc = db.collection('users').document(uid).get()
#         if user_doc.exists:
#             return jsonify({"profile": user_doc.to_dict(), "profile_complete": True}), 200
#         else:
#             return jsonify({"profile": {}, "profile_complete": False}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, request, jsonify
from app.services.firebase_service import verify_user_token, get_db

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/setup', methods=['POST'])
def setup_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_user_token(id_token)
    if not decoded:
        return jsonify({"error": "Invalid token"}), 401

    uid = decoded['uid']
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing profile data"}), 400

    try:
        db = get_db()
        db.collection('users').document(uid).set({
            "name": data.get("name", ""),
            "department": data.get("department", ""),
            "graduation_year": data.get("graduation_year"),
            "skills": data.get("skills", [])
        }, merge=True)
        return jsonify({"message": "Profile saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@profile_bp.route('/get', methods=['GET'])
def get_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_user_token(id_token)
    if not decoded:
        return jsonify({"error": "Invalid token"}), 401

    uid = decoded['uid']

    try:
        db = get_db()
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return jsonify({"profile": user_doc.to_dict(), "profile_complete": True}), 200
        else:
            return jsonify({"profile": {}, "profile_complete": False}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
