# Deck and Card API routes - handles PDF uploads, CRUD operations, and CSV exports

from flask import Blueprint, request, jsonify, make_response
from core.container import container
from flask_jwt_extended import jwt_required, get_jwt_identity
import io
import csv

# Blueprint with common prefix /api
deck_bp = Blueprint('deck', __name__, url_prefix='/api')


@deck_bp.route('/upload', methods=['POST'])
@jwt_required()  # Restricted to authenticated users
def upload_file():
    # Receive PDF file, hand it over to deck_service to extract text and generate cards using AI
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не предоставлен'}), 400
    file = request.files['file']
    mode = request.form.get('mode', 'summary')  # Card generation mode

    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    user_id = int(get_jwt_identity())
    result, status_code = container.deck_service.upload_and_generate(user_id, file, file.filename, mode)
    return jsonify(result), status_code


@deck_bp.route('/decks', methods=['GET'])
@jwt_required()  # Restricted to authenticated users
def get_decks():
    # Return a list of decks for the authenticated user with support for sorting, filtering, and pagination
    user_id = int(get_jwt_identity())
    sort_by = request.args.get('sort_by', 'newest')  # Sort parameter from URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)

    # Filter parameters
    search = request.args.get('search', '').strip() or None
    date_from = request.args.get('date_from', '').strip() or None
    date_to = request.args.get('date_to', '').strip() or None

    # Validate numerical parameters
    min_cards = request.args.get('min_cards', type=int)
    max_cards = request.args.get('max_cards', type=int)

    if sort_by not in ('newest', 'oldest', 'name', 'cards'):
        return jsonify({'error': 'Недопустимое значение sort_by'}), 400
    if page < 1:
        return jsonify({'error': 'page должен быть >= 1'}), 400
    if per_page < 1 or per_page > 50:
        return jsonify({'error': 'per_page должен быть от 1 до 50'}), 400
    if min_cards is not None and min_cards < 0:
        return jsonify({'error': 'min_cards не может быть отрицательным'}), 400
    if max_cards is not None and max_cards < 0:
        return jsonify({'error': 'max_cards не может быть отрицательным'}), 400
    if min_cards is not None and max_cards is not None and min_cards > max_cards:
        return jsonify({'error': 'min_cards не может быть больше max_cards'}), 400

    pagination = container.deck_service.get_user_decks(
        user_id, sort_by, page, per_page,
        search=search, min_cards=min_cards, max_cards=max_cards,
        date_from=date_from, date_to=date_to
    )
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
    # Return a single deck with its nested cards - accessible publicly
    deck = container.deck_service.get_deck(deck_id)
    if not deck:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(deck.to_dict(include_cards=True)), 200


@deck_bp.route('/decks/<int:deck_id>', methods=['PUT', 'DELETE'])
@jwt_required()  # Deleting or updating a deck is restricted to the deck owner
def deck_operations(deck_id):
    # Update or delete deck - ownership authorization is validated within the service layer
    user_id = int(get_jwt_identity())
    if request.method == 'PUT':
        result, status_code = container.deck_service.update_deck(deck_id, user_id, request.json)
        return jsonify(result), status_code
    elif request.method == 'DELETE':
        result, status_code = container.deck_service.delete_deck(deck_id)
        return jsonify(result), status_code


@deck_bp.route('/decks/<int:deck_id>/export', methods=['GET'])
@jwt_required()  # Export is restricted to the deck owner
def export_deck_csv(deck_id):
    # Export deck cards to a CSV format (e.g. for Anki import)
    user_id = int(get_jwt_identity())
    deck = container.deck_service.get_deck(deck_id)
    if not deck:
        return jsonify({'error': 'Not found'}), 404
    if deck.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Create CSV buffer in memory without writing to host disk
    si = io.StringIO()
    cw = csv.writer(si)
    for card in deck.cards:
        cw.writerow([card.question, card.answer])

    output = make_response(si.getvalue())
    from urllib.parse import quote
    filename = quote(f"{deck.title}.csv")  # Handle Cyrillic characters in filename encoding
    output.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


@deck_bp.route('/decks/<int:deck_id>/cards', methods=['POST'])
def create_card(deck_id):
    # Manually create a new card in the specified deck
    result, status_code = container.deck_service.create_card(deck_id, request.json)
    return jsonify(result), status_code


@deck_bp.route('/cards/<int:card_id>', methods=['PUT', 'DELETE'])
def card_operations(card_id):
    # Update or delete a specific card by its ID
    if request.method == 'PUT':
        result, status_code = container.deck_service.update_card(card_id, request.json)
        return jsonify(result), status_code
    elif request.method == 'DELETE':
        result, status_code = container.deck_service.delete_card(card_id)
        return jsonify(result), status_code
