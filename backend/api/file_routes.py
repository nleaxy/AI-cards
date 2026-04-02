# api routes для файлов колод
from flask import Blueprint, request, jsonify
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity

file_bp = Blueprint('file', __name__, url_prefix='/api')

@file_bp.route('/decks/<int:deck_id>/files', methods=['POST'])
@jwt_required()
def upload_file(deck_id):
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не предоставлен'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.upload_deck_file(deck_id, user_id, file, file.filename)
    return jsonify(result), status_code

@file_bp.route('/decks/<int:deck_id>/files', methods=['GET'])
@jwt_required()
def get_files(deck_id):
    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.get_deck_files(deck_id, user_id)
    return jsonify(result), status_code

@file_bp.route('/files/<int:file_id>/download', methods=['GET'])
@jwt_required()
def get_file_url(file_id):
    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.get_file_url(file_id, user_id)
    return jsonify(result), status_code

@file_bp.route('/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.delete_deck_file(file_id, user_id)
    return jsonify(result), status_code
