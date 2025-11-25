from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint
import os
import PyPDF2
from datetime import datetime, timedelta
from sqlalchemy import func
from config import Config
from models import db, User, Deck, Card, StudySession, UserStats
from ai_service import generate_cards_from_text

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Create tables
with app.app_context():
    db.create_all()

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Study Cards API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Swagger specification
@app.route('/api/swagger.json')
def swagger_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Study Cards API",
            "description": "API для создания учебных карточек из PDF",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:5000", "description": "Development server"}
        ],
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Service is healthy"
                        }
                    }
                }
            }
        }
    }
    return jsonify(spec)


# Auth Endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
        
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.flush()
    
    # Create stats record
    user_stats = UserStats(user_id=new_user.id)
    db.session.add(user_stats)
    
    db.session.commit()
    
    access_token = create_access_token(identity=str(new_user.id))
    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'user': new_user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
        
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/user', methods=['DELETE'])
@jwt_required()
def delete_user():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {str(e)}")
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Study Cards API is running',
        'api_key_configured': bool(Config.API_KEY)
    }), 200


# File validation
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# PDF text extraction
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Страница {page_num + 1} ---\n{page_text}"
        return text
    except Exception as e:
        raise Exception(f"Ошибка при чтении PDF: {str(e)}")


# Upload endpoint
@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не предоставлен'}), 400
    
    file = request.files['file']
    mode = request.form.get('mode', 'summary')
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Разрешены только PDF файлы'}), 400
    
    try:
        import time
        filename = f"upload_{int(time.time())}.pdf"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"Файл сохранён: {filepath}")
        
        text = extract_text_from_pdf(filepath)
        
        if not text or len(text.strip()) < 50:
            return jsonify({'error': 'Не удалось извлечь текст из PDF или текст слишком короткий'}), 400
        
        print(f"Извлечено {len(text)} символов текста")
        
        result = generate_cards_from_text(text, mode)
        
        try:
            os.remove(filepath)
        except:
            pass
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Save to DB
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        # Create deck
        deck_title = file.filename.rsplit('.', 1)[0]
        deck = Deck(
            title=deck_title,
            description=f"Карточки из файла {file.filename}",
            user_id=user.id
        )
        db.session.add(deck)
        db.session.flush()
        
        # Add cards
        created_cards = []
        for card_data in result['cards']:
            card = Card(
                question=card_data['question'],
                answer=card_data['answer'],
                source=card_data.get('source', 'Неизвестно'),
                deck_id=deck.id
            )
            db.session.add(card)
            created_cards.append(card)
        
        db.session.commit()
        
        # Update IDs in result with real DB IDs
        for i, card in enumerate(created_cards):
            result['cards'][i]['id'] = card.id

        # Increment deck counter
        user_stats = UserStats.query.filter_by(user_id=user.id).first()
        if user_stats:
            user_stats.total_decks_created += 1
            db.session.commit()
        
        result['mode'] = mode
        result['deck_id'] = deck.id
        
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Stats endpoint
@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # Get user statistics
    user_stats = UserStats.query.filter_by(user_id=user.id).first()
    
    if not user_stats:
        # Create if doesn't exist
        user_stats = UserStats(user_id=user.id)
        db.session.add(user_stats)
        db.session.commit()
    
    return jsonify(user_stats.to_dict()), 200


# Get all decks
@app.route('/api/decks', methods=['GET'])
@jwt_required()
def get_decks():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    sort_by = request.args.get('sort_by', 'newest')
    
    query = Deck.query.filter_by(user_id=user.id)
    
    if sort_by == 'newest':
        query = query.order_by(Deck.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Deck.created_at.asc())
    elif sort_by == 'name':
        query = query.order_by(Deck.title.asc())
    elif sort_by == 'cards':
        query = query.outerjoin(Card).group_by(Deck.id).order_by(func.count(Card.id).desc())
        
    decks = query.all()
    
    return jsonify({
        'decks': [deck.to_dict() for deck in decks]
    }), 200


# Get deck with cards
@app.route('/api/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    return jsonify(deck.to_dict(include_cards=True)), 200


@app.route('/api/sessions', methods=['POST'])
@jwt_required()
def create_session():
    data = request.json
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    session = StudySession(
        user_id=user.id,
        deck_id=data['deck_id'],
        cards_studied=data['cards_studied'],
        cards_correct=data['cards_correct'],
        duration_seconds=data.get('duration_seconds', 0)
    )
    
    # Get user statistics
    user_stats = UserStats.query.filter_by(user_id=user.id).first()
    if not user_stats:
        user_stats = UserStats(user_id=user.id)
        db.session.add(user_stats)
        db.session.flush()
    
    # Process card results
    for card_result in data.get('card_results', []):
        card = Card.query.get(card_result['card_id'])
        if card:
            card.times_studied += 1
            card.last_studied = datetime.utcnow()
            
            if card_result['correct']:
                card.times_correct += 1
                
                # Add to unique cards studied
                user_stats.add_unique_card(card.id)
                
                # Always try to increment streak on correct answer (model handles uniqueness)
                user_stats.increment_streak(card.id)
            else:
                # Reset streak on wrong answer
                user_stats.reset_streak()
    
    # Update deck's last studied time
    deck = Deck.query.get(data['deck_id'])
    if deck:
        deck.last_studied = datetime.utcnow()
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        **session.to_dict(),
        'user_stats': user_stats.to_dict()
    }), 201


# Reset statistics
@app.route('/api/stats/reset', methods=['POST'])
@jwt_required()
def reset_stats():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    user_stats = UserStats.query.filter_by(user_id=user.id).first()
    
    if user_stats:
        user_stats.reset_stats()
        db.session.commit()
        return jsonify({'message': 'Статистика сброшена', 'stats': user_stats.to_dict()}), 200
    
    return jsonify({'error': 'Статистика не найдена'}), 404

# Update card
@app.route('/api/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    card = Card.query.get_or_404(card_id)
    data = request.json
    
    if 'question' in data:
        card.question = data['question']
    if 'answer' in data:
        card.answer = data['answer']
    if 'source' in data:
        card.source = data['source']
    
    db.session.commit()
    return jsonify(card.to_dict()), 200


# Delete card
@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Карточка удалена'}), 200


# Create new card
@app.route('/api/decks/<int:deck_id>/cards', methods=['POST'])
def create_card(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    data = request.json
    
    card = Card(
        question=data['question'],
        answer=data['answer'],
        source=data.get('source', 'Создано вручную'),
        deck_id=deck_id
    )
    
    db.session.add(card)
    db.session.commit()
    
    return jsonify(card.to_dict()), 201

# Delete deck
@app.route('/api/decks/<int:deck_id>', methods=['DELETE'])
def delete_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    db.session.delete(deck)
    db.session.commit()
    return jsonify({'message': 'Колода удалена'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)