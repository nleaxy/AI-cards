# Route to check that the server is up and running

from flask import Blueprint, jsonify
from config import Config

# Blueprint with common prefix /api
main_bp = Blueprint('main', __name__, url_prefix='/api')


@main_bp.route('/health', methods=['GET'])
def health_check():
    # Simple health check - frontend can query this to check API server status
    return jsonify({
        'status': 'healthy',
        'message': 'Study Cards API is running',
        'api_key_configured': bool(Config.API_KEY)  # checks if the AI API key is configured
    }), 200
