from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import os
from config import Config
import PyPDF2
from ai_service import generate_cards_from_text, get_mock_stats
from models import db, User, Deck, Card, StudySession
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)

# Временная проверка (удалите после отладки)
print("=== DEBUG INFO ===")
print(f"API_KEY configured: {bool(Config.API_KEY)}")
print(f"API_KEY length: {len(Config.API_KEY) if Config.API_KEY else 0}")
print("==================")

# Инициализация БД
db.init_app(app)

# Создание таблиц
with app.app_context():
    db.create_all()
    
    # Создаём тестового пользователя если его нет
    if not User.query.filter_by(username='test_user').first():
        test_user = User(username='test_user', email='test@example.com')
        db.session.add(test_user)
        db.session.commit()
        print("Создан тестовый пользователь: test_user")

CORS(app)

# Создаём папку для загрузок
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
            },
            "/api/upload": {
                "post": {
                    "summary": "Upload PDF file and generate study cards",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        },
                                        "mode": {
                                            "type": "string",
                                            "enum": ["direct", "summary"]
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "File processed successfully"
                        }
                    }
                }
            },
            "/api/stats": {
                "get": {
                    "summary": "Get user statistics",
                    "responses": {
                        "200": {
                            "description": "Statistics retrieved"
                        }
                    }
                }
            }
        }
    }
    return jsonify(spec)


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Study Cards API is running',
        'api_key_configured': bool(Config.API_KEY)
    }), 200


# Проверка допустимых файлов
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Извлечение текста из PDF
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


# Обновлённый upload endpoint с сохранением в БД
@app.route('/api/upload', methods=['POST'])
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
        
        # Сохраняем в БД
        test_user = User.query.filter_by(username='test_user').first()
        
        # Создаём колоду
        deck_title = file.filename.rsplit('.', 1)[0]
        deck = Deck(
            title=deck_title,
            description=f"Карточки из файла {file.filename}",
            user_id=test_user.id
        )
        db.session.add(deck)
        db.session.flush()  # Получаем ID колоды
        
        # Добавляем карточки
        for card_data in result['cards']:
            card = Card(
                question=card_data['question'],
                answer=card_data['answer'],
                source=card_data.get('source', 'Неизвестно'),
                deck_id=deck.id
            )
            db.session.add(card)
        
        db.session.commit()
        
        result['mode'] = mode
        result['deck_id'] = deck.id
        
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Обновлённый stats endpoint
@app.route('/api/stats', methods=['GET'])
def get_stats():
    test_user = User.query.filter_by(username='test_user').first()
    
    total_decks = Deck.query.filter_by(user_id=test_user.id).count()
    
    # Подсчитываем изученные карточки
    cards_studied = db.session.query(db.func.sum(StudySession.cards_studied))\
        .filter_by(user_id=test_user.id).scalar() or 0
    
    # Подсчитываем streak (дней подряд)
    sessions = StudySession.query.filter_by(user_id=test_user.id)\
        .order_by(StudySession.date.desc()).all()
    
    current_streak = 0
    if sessions:
        current_date = date.today()
        for session in sessions:
            if session.date == current_date or \
               (current_date - session.date).days == current_streak:
                current_streak += 1
                current_date = session.date
            else:
                break
    
    return jsonify({
        'total_decks': total_decks,
        'cards_studied': cards_studied,
        'current_streak': current_streak
    }), 200


# Новый endpoint: получить все колоды
@app.route('/api/decks', methods=['GET'])
def get_decks():
    test_user = User.query.filter_by(username='test_user').first()
    decks = Deck.query.filter_by(user_id=test_user.id).all()
    
    return jsonify({
        'decks': [deck.to_dict() for deck in decks]
    }), 200


# Новый endpoint: получить колоду с карточками
@app.route('/api/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    return jsonify(deck.to_dict(include_cards=True)), 200


# Новый endpoint: записать результаты сессии
@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    test_user = User.query.filter_by(username='test_user').first()
    
    session = StudySession(
        user_id=test_user.id,
        deck_id=data['deck_id'],
        cards_studied=data['cards_studied'],
        cards_correct=data['cards_correct'],
        duration_seconds=data.get('duration_seconds', 0)
    )
    
    # Обновляем статистику карточек
    for card_result in data.get('card_results', []):
        card = Card.query.get(card_result['card_id'])
        if card:
            card.times_studied += 1
            if card_result['correct']:
                card.times_correct += 1
            card.last_studied = datetime.utcnow()
    
    # Обновляем время последнего изучения колоды
    deck = Deck.query.get(data['deck_id'])
    if deck:
        deck.last_studied = datetime.utcnow()
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify(session.to_dict()), 201

# Обновить карточку
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


# Удалить карточку
@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Карточка удалена'}), 200


# Создать новую карточку
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)