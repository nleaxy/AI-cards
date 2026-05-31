# Admin API routes - restricted to users with the 'admin' role

from flask import Blueprint, request, jsonify
from core.security import admin_required  # decorator that verifies the current user has the 'admin' role
from models import User, db

# Blueprint with prefix /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required  # verify that the user is an admin
def get_all_users():
    # Return a list of all users in the system - admin only
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required  # verify that the user is an admin
def update_user_role(user_id):
    # Change the user's role - an admin can assign 'user' or 'admin' to another user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    new_role = data.get('role')

    # Allow only valid roles
    if new_role not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400

    user.role = new_role
    db.session.commit()
    return jsonify({'message': 'User role updated', 'user': user.to_dict()}), 200
