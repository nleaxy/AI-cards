# api routes для администратора - только для пользователей с ролью admin

from flask import Blueprint, request, jsonify
from core.security import admin_required  # декоратор-охранник, проверяет что ты admin
from models import User, db

# blueprint с префиксом /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required  # проверяем что текущий пользователь - администратор
def get_all_users():
    # возвращаем список всех пользователей в системе - только для admin
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required  # проверяем что текущий пользователь - администратор
def update_user_role(user_id):
    # меняем роль пользователя - admin может назначить user или admin другому
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    new_role = data.get('role')

    # разрешаем только эти две роли
    if new_role not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400

    user.role = new_role
    db.session.commit()
    return jsonify({'message': 'User role updated', 'user': user.to_dict()}), 200
