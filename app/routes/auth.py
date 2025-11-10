from flask import Blueprint, request, jsonify
from app.services.firebase_service import (
    verify_user_token,
    get_user,
    create_user,
    login_with_email_password
)
from firebase_admin import auth as admin_auth
import requests
from flask import current_app

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    id_token = data.get("id_token")
    email = data.get("email")
    password = data.get("password")

    # Option 1: If frontend sends id_token directly
    if id_token:
        decoded = verify_user_token(id_token)
        if not decoded:
            return jsonify({"error": "Invalid token"}), 401
        return _handle_user(decoded, id_token=id_token)

    # Option 2: Email/password login via Firebase REST API
    elif email and password:
        result = login_with_email_password(email, password)
        if not result:
            return jsonify({"error": "Invalid email/password"}), 401

        decoded = verify_user_token(result["id_token"])
        if not decoded:
            return jsonify({"error": "Could not verify Firebase token"}), 401

        return _handle_user(
            decoded,
            id_token=result["id_token"],
            refresh_token=result.get("refresh_token")
        )

    return jsonify({"error": "Missing id_token or email/password"}), 400


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new Firebase user and Firestore document"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        user_record = admin_auth.create_user(email=email, password=password, display_name=name)
        user_data = {"email": email, "name": name, "uid": user_record.uid}
        create_user(user_record.uid, user_data)
        return jsonify({"message": "User registered successfully", "user": user_data}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 400


@auth_bp.route("/profile", methods=["GET"])
def profile():
    """Returns the currently authenticated user's info"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    id_token = auth_header.split(" ")[1]
    decoded = verify_user_token(id_token)
    if not decoded:
        return jsonify({"error": "Invalid token"}), 401

    user = get_user(decoded["uid"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user}), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh an expired Firebase ID token using refresh_token"""
    data = request.get_json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Missing refresh_token"}), 400

    url = f"https://securetoken.googleapis.com/v1/token?key={current_app.config['FIREBASE_API_KEY']}"
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    r = requests.post(url, data=payload)
    return jsonify(r.json()), r.status_code


def _handle_user(decoded, id_token=None, refresh_token=None):
    uid = decoded["uid"]
    user = get_user(uid)
    if not user:
        user_data = {"email": decoded.get("email"), "name": decoded.get("name", ""), "uid": uid}
        create_user(uid, user_data)
        user = user_data

    response = {"message": "Login successful", "user": user}
    if id_token:
        response["id_token"] = id_token
    if refresh_token:
        response["refresh_token"] = refresh_token
    return jsonify(response), 200
