from flask import Blueprint, request, jsonify
from security import authenticate_user, create_user, delete_user, change_password, require_auth, require_admin, get_users_db

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    auth_result = authenticate_user(username, password)
    
    if auth_result:
        return jsonify(auth_result), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def list_users():
    """List all users (admin only)"""
    users = get_users_db()
    
    # Remove sensitive information
    sanitized_users = {}
    for username, user_data in users.items():
        sanitized_users[username] = {
            "username": username,
            "is_admin": user_data.get("is_admin", False),
            "created_at": user_data.get("created_at"),
            "created_by": user_data.get("created_by")
        }
    
    return jsonify(sanitized_users), 200

@auth_bp.route('/users', methods=['POST'])
@require_auth
@require_admin
def create_new_user():
    """Create a new user (admin only)"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    success, message = create_user(
        username, 
        password, 
        is_admin=is_admin, 
        created_by=request.user.get("username")
    )
    
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 400

@auth_bp.route('/users/<username>', methods=['DELETE'])
@require_auth
@require_admin
def delete_existing_user(username):
    """Delete a user (admin only)"""
    success, message = delete_user(username)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

@auth_bp.route('/users/<username>/change-password', methods=['POST'])
@require_auth
def update_password(username):
    """Change a user's password"""
    # Check if user is trying to change their own password or is an admin
    if username != request.user.get("username") and not request.user.get("is_admin", False):
        return jsonify({"error": "You can only change your own password"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password:
        return jsonify({"error": "Missing new password"}), 400
    
    success, message = change_password(username, new_password)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user's info"""
    user = request.user
    
    # Remove sensitive information
    sanitized_user = {
        "username": user.get("username"),
        "is_admin": user.get("is_admin", False),
        "created_at": user.get("created_at")
    }
    
    return jsonify(sanitized_user), 200 