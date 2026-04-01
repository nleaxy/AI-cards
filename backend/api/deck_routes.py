# api routes для колод и карточек - загрузка pdf, crud операции, экспорт в csv

from flask import Blueprint, request, jsonify, make_response
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity
import io
import csv

# blueprint с общим префиксом /api
deck_bp = Blueprint('deck', __name__, url_prefix='/api')


@deck_bp.route('/upload', methods=['POST'])
@jwt_required()  # только авторизованный пользователь может загружать файлы
def upload_file():
    # принимаем pdf файл, передаем в deck_service который вытащит текст и создаст карточки через ai
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не предоставлен'}), 400
    file = request.files['file']
    mode = request.form.get('mode', 'summary')  # режим генерации карточек

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.upload_and_generate(user_id, file, file.filename, mode)
    return jsonify(result), status_code


@deck_bp.route('/decks', methods=['GET'])
@jwt_required()  # только авторизованный видит свои колоды
def get_decks():
    # возвращаем список колод текущего пользователя с поддержкой сортировки и постраничности
    user_id = int(get_jwt_identity())
    sort_by = request.args.get('sort_by', 'newest')  # параметр сортировки из url
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)

    pagination = container.deck_service.get_user_decks(user_id, sort_by, page, per_page)
    decks = pagination.items
    return jsonify({
        'decks': [deck.to_dict() for deck in decks],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@deck_bp.route('/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    # возвращаем одну колоду со всеми ее карточками - доступно без авторизации
    deck = container.deck_service.get_deck(deck_id)
    if not deck:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(deck.to_dict(include_cards=True)), 200


@deck_bp.route('/decks/<int:deck_id>', methods=['PUT', 'DELETE'])
@jwt_required()  # изменять и удалять колоду может только авторизованный владелец
def deck_operations(deck_id):
    # обновляем или удаляем колоду - проверка что ты владелец происходит внутри сервиса
    user_id = int(get_jwt_identity())
    if request.method == 'PUT':
        result, status_code = container.deck_service.update_deck(deck_id, user_id, request.json)
        return jsonify(result), status_code
    elif request.method == 'DELETE':
        result, status_code = container.deck_service.delete_deck(deck_id)
        return jsonify(result), status_code


@deck_bp.route('/decks/<int:deck_id>/export', methods=['GET'])
@jwt_required()  # экспорт только для владельца колоды
def export_deck_csv(deck_id):
    # экспортируем карточки колоды в csv файл для использования в anki и тд
    user_id = int(get_jwt_identity())
    deck = container.deck_service.get_deck(deck_id)
    if not deck:
        return jsonify({'error': 'Not found'}), 404
    if deck.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # создаем csv прямо в памяти без сохранения на диск
    si = io.StringIO()
    cw = csv.writer(si)
    for card in deck.cards:
        cw.writerow([card.question, card.answer])

    output = make_response(si.getvalue())
    from urllib.parse import quote
    filename = quote(f"{deck.title}.csv")  # обрабатываем кириллицу в названии
    output.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


@deck_bp.route('/decks/<int:deck_id>/cards', methods=['POST'])
def create_card(deck_id):
    # создаем новую карточку вручную в указанной колоде
    result, status_code = container.deck_service.create_card(deck_id, request.json)
    return jsonify(result), status_code


@deck_bp.route('/cards/<int:card_id>', methods=['PUT', 'DELETE'])
def card_operations(card_id):
    # обновляем или удаляем конкретную карточку по её id
    if request.method == 'PUT':
        result, status_code = container.deck_service.update_card(card_id, request.json)
        return jsonify(result), status_code
    elif request.method == 'DELETE':
        result, status_code = container.deck_service.delete_card(card_id)
        return jsonify(result), status_code
