# Decorators for Access Control (RBAC)
# Applying @admin_required to a route automatically verifies the user's role before execution

from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User


def role_required(required_role):
    # Decorator factory: accepts a required role and returns the actual decorator
    def decorator(fn):
        @wraps(fn)
        @jwt_required()  # First, verify that a valid JWT token is present
        def wrapper(*args, **kwargs):
            # Extract the user ID from the JWT token identity
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Admin bypasses all checks; regular user is authorized only if they have the required role
            if user.role != required_role and user.role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return role_required('admin')(fn)
