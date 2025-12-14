from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_swagger_ui import get_swaggerui_blueprint
import os
import PyPDF2
import csv
import io
from minio import Minio
from datetime import datetime
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
    # Auto-migration for emoji column
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE decks ADD COLUMN emoji VARCHAR(10)"))
            conn.commit()
            print("Added emoji column to decks table")
    except Exception:
        pass # Column likely already exists

# Initialize MinIO Client
minio_client = Minio(
    app.config['MINIO_ENDPOINT'],
    access_key=app.config['MINIO_ACCESS_KEY'],
    secret_key=app.config['MINIO_SECRET_KEY'],
    secure=app.config['MINIO_SECURE']
)

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
            "description": "API для создания учебных карточек из PDF с использованием AI",
            "version": "2.0.0",
            "contact": {
                "name": "Study Cards Support",
                "email": "support@studycards.com"
            }
        },
        "servers": [
            {"url": "http://localhost:5000", "description": "Development server"}
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"}
                    }
                },
                "Deck": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "user_id": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "last_studied": {"type": "string", "format": "date-time"},
                        "card_count": {"type": "integer"}
                    }
                },
                "Card": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                        "source": {"type": "string"},
                        "deck_id": {"type": "integer"},
                        "times_studied": {"type": "integer"},
                        "times_correct": {"type": "integer"},
                        "accuracy": {"type": "number"}
                    }
                },
                "UserStats": {
                    "type": "object",
                    "properties": {
                        "total_decks": {"type": "integer"},
                        "cards_studied": {"type": "integer"},
                        "max_streak": {"type": "integer"},
                        "current_streak": {"type": "integer"}
                    }
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"}
                    }
                }
            }
        },
        "paths": {
            "/api/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Проверка состояния API",
                    "description": "Возвращает статус работы сервера и наличие API ключа",
                    "responses": {
                        "200": {
                            "description": "API работает корректно",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "message": {"type": "string"},
                                            "api_key_configured": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Регистрация нового пользователя",
                    "description": "Создаёт нового пользователя и возвращает JWT токен",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "email", "password"],
                                    "properties": {
                                        "username": {"type": "string", "example": "john_doe"},
                                        "email": {"type": "string", "format": "email", "example": "john@example.com"},
                                        "password": {"type": "string", "format": "password", "example": "SecurePass123"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Пользователь успешно зарегистрирован",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "access_token": {"type": "string"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Ошибка валидации или пользователь уже существует",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Вход в систему",
                    "description": "Аутентификация пользователя и получение JWT токена",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {"type": "string", "example": "john_doe"},
                                        "password": {"type": "string", "format": "password", "example": "SecurePass123"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Успешный вход",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "access_token": {"type": "string"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Неверные учётные данные",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/user": {
                "delete": {
                    "tags": ["Authentication"],
                    "summary": "Удалить текущего пользователя",
                    "description": "Удаляет учётную запись текущего пользователя и все связанные данные",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Пользователь успешно удалён",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "Не авторизован"},
                        "404": {"description": "Пользователь не найден"}
                    }
                }
            },
            "/api/upload": {
                "post": {
                    "tags": ["Decks"],
                    "summary": "Загрузить PDF и создать карточки",
                    "description": "Загружает PDF файл, извлекает текст и генерирует учебные карточки с помощью AI",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "PDF файл (макс. 16MB)"
                                        },
                                        "mode": {
                                            "type": "string",
                                            "enum": ["direct", "summary"],
                                            "default": "summary",
                                            "description": "Режим: 'summary' - с кратким обзором, 'direct' - сразу карточки"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Файл успешно обработан, карточки созданы",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "mode": {"type": "string"},
                                            "deck_id": {"type": "integer"},
                                            "cards": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Card"}
                                            },
                                            "total_cards": {"type": "integer"},
                                            "summary": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "title": {"type": "string"},
                                                        "content": {"type": "string"},
                                                        "source": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Ошибка валидации файла"},
                        "401": {"description": "Не авторизован"},
                        "500": {"description": "Ошибка обработки файла"}
                    }
                }
            },
            "/api/decks": {
                "get": {
                    "tags": ["Decks"],
                    "summary": "Получить все колоды пользователя",
                    "description": "Возвращает список колод с возможностью сортировки",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "sort_by",
                            "in": "query",
                            "description": "Критерий сортировки",
                            "schema": {
                                "type": "string",
                                "enum": ["newest", "oldest", "name", "cards"],
                                "default": "newest"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Список колод",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "decks": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Deck"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "Не авторизован"}
                    }
                }
            },
            "/api/decks/{deck_id}": {
                "get": {
                    "tags": ["Decks"],
                    "summary": "Получить колоду с карточками",
                    "description": "Возвращает детальную информацию о колоде включая все карточки",
                    "parameters": [
                        {
                            "name": "deck_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                            "description": "ID колоды"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Детали колоды",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "allOf": [
                                            {"$ref": "#/components/schemas/Deck"},
                                            {
                                                "type": "object",
                                                "properties": {
                                                    "cards": {
                                                        "type": "array",
                                                        "items": {"$ref": "#/components/schemas/Card"}
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        "404": {"description": "Колода не найдена"}
                    }
                },
                "delete": {
                    "tags": ["Decks"],
                    "summary": "Удалить колоду",
                    "description": "Удаляет колоду и все связанные карточки",
                    "parameters": [
                        {
                            "name": "deck_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Колода удалена",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "Колода не найдена"}
                    }
                }
            },
            "/api/decks/{deck_id}/cards": {
                "post": {
                    "tags": ["Cards"],
                    "summary": "Создать новую карточку",
                    "description": "Добавляет новую карточку в указанную колоду",
                    "parameters": [
                        {
                            "name": "deck_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["question", "answer"],
                                    "properties": {
                                        "question": {"type": "string", "example": "Что такое React?"},
                                        "answer": {"type": "string", "example": "React - это JavaScript библиотека"},
                                        "source": {"type": "string", "example": "Страница 1", "default": "Создано вручную"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Карточка создана",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Card"}
                                }
                            }
                        },
                        "404": {"description": "Колода не найдена"}
                    }
                }
            },
            "/api/cards/{card_id}": {
                "put": {
                    "tags": ["Cards"],
                    "summary": "Обновить карточку",
                    "description": "Изменяет содержимое карточки",
                    "parameters": [
                        {
                            "name": "card_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string"},
                                        "answer": {"type": "string"},
                                        "source": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Карточка обновлена",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Card"}
                                }
                            }
                        },
                        "404": {"description": "Карточка не найдена"}
                    }
                },
                "delete": {
                    "tags": ["Cards"],
                    "summary": "Удалить карточку",
                    "description": "Удаляет карточку из колоды",
                    "parameters": [
                        {
                            "name": "card_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Карточка удалена",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "Карточка не найдена"}
                    }
                }
            },
            "/api/sessions": {
                "post": {
                    "tags": ["Study"],
                    "summary": "Записать результаты сессии обучения",
                    "description": "Сохраняет результаты изучения карточек и обновляет статистику",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["deck_id", "cards_studied", "cards_correct", "card_results"],
                                    "properties": {
                                        "deck_id": {"type": "integer", "example": 1},
                                        "cards_studied": {"type": "integer", "example": 10},
                                        "cards_correct": {"type": "integer", "example": 8},
                                        "duration_seconds": {"type": "integer", "example": 300},
                                        "card_results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "card_id": {"type": "integer"},
                                                    "correct": {"type": "boolean"},
                                                    "is_streak_card": {"type": "boolean"},
                                                    "reset_streak": {"type": "boolean"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Сессия сохранена",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "user_id": {"type": "integer"},
                                            "deck_id": {"type": "integer"},
                                            "date": {"type": "string", "format": "date"},
                                            "cards_studied": {"type": "integer"},
                                            "cards_correct": {"type": "integer"},
                                            "accuracy": {"type": "number"},
                                            "user_stats": {"$ref": "#/components/schemas/UserStats"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "Не авторизован"}
                    }
                }
            },
            "/api/stats": {
                "get": {
                    "tags": ["Statistics"],
                    "summary": "Получить статистику пользователя",
                    "description": "Возвращает общую статистику обучения пользователя",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Статистика пользователя",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserStats"}
                                }
                            }
                        },
                        "401": {"description": "Не авторизован"}
                    }
                }
            },
            "/api/stats/reset": {
                "post": {
                    "tags": ["Statistics"],
                    "summary": "Сбросить статистику",
                    "description": "Обнуляет всю статистику пользователя (колоды и карточки не удаляются)",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Статистика сброшена",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"},
                                            "stats": {"$ref": "#/components/schemas/UserStats"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "Не авторизован"},
                        "404": {"description": "Статистика не найдена"}
                    }
                }
            }
        }
    }
    return jsonify(spec)


# Auth Endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя
    ---
    Создаёт учётную запись пользователя, генерирует JWT токен и инициализирует статистику
    """
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
    """
    Вход в систему
    ---
    Аутентифицирует пользователя и возвращает JWT токен
    """
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
    """
    Удаление пользователя
    ---
    Удаляет текущего пользователя и все связанные данные (колоды, карточки, статистику)
    """
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
    """
    Проверка состояния API
    ---
    Возвращает информацию о работе сервера и конфигурации
    """
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
# PDF text extraction
def extract_text_from_pdf(file_source):
    text = ""
    try:
        # Check if file_source is a path or a stream
        if isinstance(file_source, str):
            file_obj = open(file_source, 'rb')
        else:
            file_obj = file_source # Assume it's a stream (BytesIO)

        pdf_reader = PyPDF2.PdfReader(file_obj)
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Страница {page_num + 1} ---\n{page_text}"
        
        if isinstance(file_source, str):
            file_obj.close()
            
        return text
    except Exception as e:
        raise Exception(f"Ошибка при чтении PDF: {str(e)}")


# Upload endpoint
@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """
    Загрузка PDF и генерация карточек
    ---
    Принимает PDF файл, извлекает текст и генерирует учебные карточки с помощью AI
    """
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
        timestamp = int(time.time())
        filename = f"upload_{timestamp}.pdf"
        
        # Read file content
        file_content = file.read()
        file_size = len(file_content)
        file_stream = io.BytesIO(file_content)
        
        # Upload to MinIO
        bucket_name = app.config['MINIO_BUCKET']
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
            
            minio_client.put_object(
                bucket_name,
                filename,
                io.BytesIO(file_content),
                length=file_size,
                content_type='application/pdf'
            )
            print(f"Файл загружен в MinIO: {bucket_name}/{filename}")
        except Exception as e:
            print(f"Ошибка загрузки в MinIO: {e}")
            # Continue processing even if upload fails, but log it
            
        # Extract text from stream
        file_stream.seek(0)
        text = extract_text_from_pdf(file_stream)
        
        if not text or len(text.strip()) < 50:
            return jsonify({'error': 'Не удалось извлечь текст из PDF или текст слишком короткий'}), 400
        
        print(f"Извлечено {len(text)} символов текста")
        
        result = generate_cards_from_text(text, mode)
        
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
    """
    Получение статистики пользователя
    ---
    Возвращает общую статистику обучения (колоды, карточки, серии)
    """
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
    """
    Получение всех колод пользователя
    ---
    Возвращает список колод с возможностью сортировки и пагинации
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    
    query = Deck.query.filter_by(user_id=user.id)
    
    if sort_by == 'newest':
        query = query.order_by(Deck.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Deck.created_at.asc())
    elif sort_by == 'name':
        query = query.order_by(Deck.title.asc())
    elif sort_by == 'cards':
        query = query.outerjoin(Card).group_by(Deck.id).order_by(func.count(Card.id).desc())
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    decks = pagination.items
    
    return jsonify({
        'decks': [deck.to_dict() for deck in decks],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


# Get deck with cards
@app.route('/api/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    """
    Получение колоды с карточками
    ---
    Возвращает детальную информацию о колоде включая все карточки
    """
    deck = Deck.query.get_or_404(deck_id)
    return jsonify(deck.to_dict(include_cards=True)), 200


@app.route('/api/decks/<int:deck_id>', methods=['PUT'])
@jwt_required()
def update_deck(deck_id):
    """
    Обновление колоды (название, описание, эмодзи)
    ---
    Обновляет метаданные колоды
    """
    current_user_id = int(get_jwt_identity())
    deck = Deck.query.get_or_404(deck_id)
    
    if deck.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    if 'title' in data:
        deck.title = data['title']
    if 'description' in data:
        deck.description = data['description']
    if 'emoji' in data:
        deck.emoji = data['emoji']
        
    db.session.commit()
    return jsonify(deck.to_dict()), 200


@app.route('/api/decks/<int:deck_id>/export', methods=['GET'])
@jwt_required()
def export_deck_csv(deck_id):
    """
    Экспорт колоды в CSV для Anki
    ---
    Возвращает CSV файл с карточками колоды (Front, Back)
    """
    current_user_id = int(get_jwt_identity())
    deck = Deck.query.get_or_404(deck_id)
    
    if deck.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Write cards
    for card in deck.cards:
        cw.writerow([card.question, card.answer])
        
    output = make_response(si.getvalue())
    # Encode filename to handle non-ASCII characters
    from urllib.parse import quote
    filename = quote(f"{deck.title}.csv")
    
    output.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


@app.route('/api/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """
    Сохранение результатов сессии обучения
    ---
    Записывает результаты изучения карточек и обновляет статистику пользователя
    """
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
    """
    Сброс статистики пользователя
    ---
    Обнуляет всю статистику обучения (колоды и карточки не удаляются)
    """
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
    """
    Обновление карточки
    ---
    Изменяет содержимое существующей карточки
    """
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
    """
    Удаление карточки
    ---
    Удаляет карточку из колоды
    """
    card = Card.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Карточка удалена'}), 200


# Create new card
@app.route('/api/decks/<int:deck_id>/cards', methods=['POST'])
def create_card(deck_id):
    """
    Создание новой карточки
    ---
    Добавляет новую карточку в указанную колоду
    """
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
    """
    Удаление колоды
    ---
    Удаляет колоду и все связанные карточки
    """
    deck = Deck.query.get_or_404(deck_id)
    db.session.delete(deck)
    db.session.commit()
    return jsonify({'message': 'Колода удалена'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)