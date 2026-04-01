# маршрут для проверки что сервер запущен и работает

from flask import Blueprint, jsonify
from config import Config

# blueprint с общим префиксом /api
main_bp = Blueprint('main', __name__, url_prefix='/api')


@main_bp.route('/health', methods=['GET'])
def health_check():
    # простая проверка что api живой - фронтенд может отсюда узнать статус сервера
    return jsonify({
        'status': 'healthy',
        'message': 'Study Cards API is running',
        'api_key_configured': bool(Config.API_KEY)  # есть ли ключ для ai
    }), 200
