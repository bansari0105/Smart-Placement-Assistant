# from flask import Flask, jsonify
# from app.config import Config
# from app.services.firebase_service import init_firebase

# # 1️⃣ Create Flask app
# app = Flask(__name__)
# app.config.from_object(Config)

# # 2️⃣ Initialize Firebase BEFORE importing any routes
# init_firebase(app)

# # 3️⃣ Import blueprints AFTER Firebase is initialized
# from app.routes.auth import auth_bp
# from app.routes.users import users_bp
# from app.routes.applications import applications_bp
# from app.routes.profile import profile_bp
# from app.routes.companies import companies_bp

# # 4️⃣ Register blueprints
# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(users_bp, url_prefix='/users')
# app.register_blueprint(applications_bp, url_prefix='/applications')
# app.register_blueprint(profile_bp, url_prefix='/profile')
# app.register_blueprint(companies_bp, url_prefix='/companies')

# # 5️⃣ Optional test route
# @app.route('/')
# def home():
#     return jsonify({"message": "home route working"})

# if __name__ == "__main__":
#     app.run(debug=True, host="127.0.0.1", port=5000)


from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.services.firebase_service import init_firebase

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for Flutter app (before routes)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔑 Fail fast if FIREBASE_API_KEY is not set
if not app.config.get("FIREBASE_API_KEY"):
    raise RuntimeError("❌ FIREBASE_API_KEY missing! Please set it in Config or environment variables.")

# Initialize Firebase BEFORE importing any routes
init_firebase(app)

# Import blueprints AFTER Firebase init
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.applications import applications_bp
from app.routes.profile import profile_bp
from app.routes.companies import companies_bp
from app.routes.calender import calender_bp
from app.routes.chat import chat_bp
from app.routes.chatbot import chatbot_bp
from app.routes.notifications import notifications_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(applications_bp, url_prefix="/applications")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(companies_bp, url_prefix="/companies")
app.register_blueprint(calender_bp, url_prefix="/calendar")
app.register_blueprint(chat_bp, url_prefix="/chat")
app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
app.register_blueprint(notifications_bp, url_prefix="/notifications")

@app.route("/")
def home():
    return jsonify({"message": "home route working"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
