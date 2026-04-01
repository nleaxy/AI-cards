# декораторы для проверки прав доступа (rbac - role based access control)
# вешаем @admin_required на функцию и она автоматически проверяет роль перед выполнением

from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User


def role_required(required_role):
    # декоратор-фабрика: принимает нужную роль и возвращает декоратор-проверку
    def decorator(fn):
        @wraps(fn)
        @jwt_required()  # сначала проверяем что токен валидный вообще
        def wrapper(*args, **kwargs):
            # достаем id пользователя из jwt токена
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # admin может делать всё, обычный user - только если у него нужная роль
            if user.role != required_role and user.role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return role_required('admin')(fn)
