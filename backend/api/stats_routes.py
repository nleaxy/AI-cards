# Statistics API routes - handles retrieving, resetting, and saving study session statistics

from flask import Blueprint, request, jsonify
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity

# Blueprint with common prefix /api
stats_bp = Blueprint('stats', __name__, url_prefix='/api')


@stats_bp.route('/sessions', methods=['POST'])
@jwt_required()  # Restricted to authenticated users
def create_session():
    # Save study session results (correct answers count, streaks, etc.)
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.create_session(user_id, request.json)
    return jsonify(result), status_code


@stats_bp.route('/stats', methods=['GET'])
@jwt_required()  # Restricted to authenticated users
def get_stats():
    # Retrieve statistics for the authenticated user (streaks, card count, accuracy)
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.get_stats(user_id)
    return jsonify(result), status_code


@stats_bp.route('/stats/reset', methods=['POST'])
@jwt_required()  # Restricted to authenticated users
def reset_stats():
    # Reset user statistics to zero (leaves decks and cards intact)
    user_id = int(get_jwt_identity())
    result, status_code = container.stats_service.reset_stats(user_id)
    return jsonify(result), status_code
