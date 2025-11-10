# import firebase_admin
# from firebase_admin import credentials, auth, firestore
# import requests

# cred = None
# default_app = None
# db = None
# FIREBASE_API_KEY = None

# def init_firebase(app):
#     global cred, default_app, db, FIREBASE_API_KEY
#     cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
#     default_app = firebase_admin.initialize_app(cred)
#     db = firestore.client()
#     FIREBASE_API_KEY = app.config.get('FIREBASE_API_KEY')


# def verify_user_token(id_token):
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token
#     except Exception as e:
#         print(f"Error verifying token: {e}")
#         return None


# def get_user(uid):
#     try:
#         user_doc = db.collection('users').document(uid).get()
#         if user_doc.exists:
#             return user_doc.to_dict()
#         return None
#     except Exception as e:
#         print(f"Error fetching user: {e}")
#         return None


# def create_user(uid, user_data):
#     try:
#         db.collection('users').document(uid).set(user_data)
#         return True
#     except Exception as e:
#         print(f"Error creating user: {e}")
#         return False


# def login_with_email_password(email, password):
#     """Use Firebase REST API to sign in and get ID token."""
#     global FIREBASE_API_KEY
#     if not FIREBASE_API_KEY:
#         raise ValueError("FIREBASE_API_KEY not set in config")

#     url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
#     payload = {"email": email, "password": password, "returnSecureToken": True}

#     try:
#         response = requests.post(url, json=payload)
#         data = response.json()

#         if response.status_code == 200 and "idToken" in data:
#             return {
#                 "id_token": data["idToken"],
#                 "refresh_token": data.get("refreshToken"),
#                 "local_id": data.get("localId"),
#                 "email": data.get("email")
#             }
#         else:
#             print(f"Firebase login error: {data}")
#             return None
#     except Exception as e:
#         print(f"Error logging in with Firebase: {e}")
#         return None

# import firebase_admin
# from firebase_admin import credentials, auth, firestore
# import requests

# # Global variables
# cred = None
# default_app = None
# db = None  # Firestore client
# FIREBASE_API_KEY = None

# def init_firebase(app):
#     """
#     Initialize Firebase app and Firestore DB.
#     Call this once in your Flask app before using `db`.
#     """
#     global cred, default_app, db, FIREBASE_API_KEY
#     if not firebase_admin._apps:  # prevent duplicate initialization
#         cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
#         default_app = firebase_admin.initialize_app(cred)
#     db = firestore.client()  # db is now Firestore client object
#     FIREBASE_API_KEY = app.config.get('FIREBASE_API_KEY')


# def verify_user_token(id_token):
#     """
#     Verify Firebase user ID token.
#     Returns decoded token dict or None if invalid.
#     """
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token
#     except Exception as e:
#         print(f"Error verifying token: {e}")
#         return None


# def get_user(uid):
#     """
#     Fetch user document from Firestore by UID.
#     """
#     if db is None:
#         raise RuntimeError("Firestore DB not initialized. Call init_firebase(app) first.")
#     try:
#         doc = db.collection('users').document(uid).get()
#         return doc.to_dict() if doc.exists else None
#     except Exception as e:
#         print(f"Error fetching user: {e}")
#         return None


# def create_user(uid, user_data):
#     """
#     Create or update a user document in Firestore.
#     """
#     if db is None:
#         raise RuntimeError("Firestore DB not initialized. Call init_firebase(app) first.")
#     try:
#         db.collection('users').document(uid).set(user_data)
#         return True
#     except Exception as e:
#         print(f"Error creating user: {e}")
#         return False


# def login_with_email_password(email, password):
#     """
#     Login user using Firebase Auth REST API.
#     Returns dict with id_token, refresh_token, local_id, email or None on failure.
#     """
#     global FIREBASE_API_KEY
#     if not FIREBASE_API_KEY:
#         raise ValueError("FIREBASE_API_KEY not set in config")

#     url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
#     payload = {"email": email, "password": password, "returnSecureToken": True}

#     try:
#         response = requests.post(url, json=payload)
#         data = response.json()
#         if response.status_code == 200 and "idToken" in data:
#             return {
#                 "id_token": data["idToken"],
#                 "refresh_token": data.get("refreshToken"),
#                 "local_id": data.get("localId"),
#                 "email": data.get("email")
#             }
#         else:
#             print(f"Firebase login error: {data}")
#             return None
#     except Exception as e:
#         print(f"Error logging in with Firebase: {e}")
#         return None

# --- Existing imports ---
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask import request, jsonify
import requests
from functools import wraps

# --- Existing global variables & functions ---
cred = None
default_app = None
db = None  # Firestore client
FIREBASE_API_KEY = None

def init_firebase(app):
    global cred, default_app, db, FIREBASE_API_KEY
    if not firebase_admin._apps:
        cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS'])
        default_app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    FIREBASE_API_KEY = app.config.get('FIREBASE_API_KEY')


def verify_user_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"[Firebase] Token verification failed: {e}")
        return None


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1]
        decoded_token = verify_user_token(token)
        if not decoded_token:
            return jsonify({"error": "Could not verify Firebase token"}), 401

        request.user = decoded_token
        return f(*args, **kwargs)
    return decorated_function


def get_db():
    if db is None:
        raise RuntimeError("Firestore DB not initialized. Call init_firebase(app) first.")
    return db


def get_user(uid):
    db_client = get_db()
    try:
        doc = db_client.collection('users').document(uid).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"[Firebase] Error fetching user: {e}")
        return None


def create_user(uid, user_data):
    db_client = get_db()
    try:
        db_client.collection('users').document(uid).set(user_data)
        return True
    except Exception as e:
        print(f"[Firebase] Error creating user: {e}")
        return False


def login_with_email_password(email, password):
    global FIREBASE_API_KEY
    if not FIREBASE_API_KEY:
        raise ValueError("FIREBASE_API_KEY not set in config")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if response.status_code == 200 and "idToken" in data:
            return {
                "id_token": data["idToken"],
                "refresh_token": data.get("refreshToken"),
                "local_id": data.get("localId"),
                "email": data.get("email")
            }
        else:
            print(f"[Firebase] Login failed: {data}")
            return None
    except Exception as e:
        print(f"[Firebase] Error logging in with email/password: {e}")
        return None


# =========================
# Calendar / Application Logic
# =========================

def apply_for_company(user_id, company_name, date="2025-09-30", time="10:00 AM"):
    """
    Stores application and auto-creates a calendar event.
    """
    db_client = get_db()
    try:
        # 1️⃣ Save application
        db_client.collection("applications").add({
            "userId": user_id,
            "company": company_name,
            "status": "applied"
        })

        # 2️⃣ Auto-create calendar event
        event_data = {
            "title": f"Applied to {company_name}",
            "date": date,
            "time": time,
            "description": f"Application submitted for {company_name}",
            "userId": user_id
        }
        db_client.collection("events").add(event_data)

        return True
    except Exception as e:
        print(f"[Firebase] Error applying for company: {e}")
        return False


def get_user_events(user_id):
    """
    Fetch all calendar events for a specific user
    """
    db_client = get_db()
    try:
        events_ref = db_client.collection("events").where("userId", "==", user_id).stream()
        events = [e.to_dict() for e in events_ref]
        return events
    except Exception as e:
        print(f"[Firebase] Error fetching user events: {e}")
        return []
