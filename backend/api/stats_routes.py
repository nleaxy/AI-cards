# api routes для статистики - получение, сброс и сохранение результатов учебной сессии

from flask import Blueprint, request, jsonify
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity

# blueprint с общим префиксом /api
stats_bp = Blueprint('stats', __name__, url_prefix='/api')


@stats_bp.route('/sessions', methods=['POST'])
@jwt_required()  # нужно быть авторизованным чтобы сохранить сессию
def create_session():
    # сохраняем результаты учебной сессии - сколько правильно ответил, стрики и тд
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.create_session(user_id, request.json)
    return jsonify(result), status_code


@stats_bp.route('/stats', methods=['GET'])
@jwt_required()  # только свою статистику можно посмотреть
def get_stats():
    # возвращаем статистику текущего пользователя - стрики, количество карточек и тд
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.get_stats(user_id)
    return jsonify(result), status_code


@stats_bp.route('/stats/reset', methods=['POST'])
@jwt_required()  # только сам пользователь может сбросить свою статистику
def reset_stats():
    # сбрасываем всю статистику пользователя в ноль (колоды и карточки остаются)
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.reset_stats(user_id)
    return jsonify(result), status_code
