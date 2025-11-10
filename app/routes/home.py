from flask import Blueprint, jsonify

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET'])
def get_users():
    return jsonify({"message": "home route working"})