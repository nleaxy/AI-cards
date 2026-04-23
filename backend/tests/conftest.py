# Базовые настройки тестов и фикстуры, включая изолированную БД в памяти
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app
from models import db
from config import Config

class TestConfig(Config):
    # Конфигурация приложения специально для тестов (БД в оперативке, токены)
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-jwt-secret'
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    # Создает само приложение и все таблицы в тестовой базе данных
    flask_app.config.from_object(TestConfig)
    with flask_app.app_context():
        db.create_all()
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Ручное создание/обновление таблиц и колонок для совместимости
            try:
                conn.execute(text("ALTER TABLE decks ADD COLUMN emoji VARCHAR(10)"))
                conn.commit()
            except Exception:
                pass
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    expires_at DATETIME NOT NULL,
                    revoked BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS deck_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deck_id INTEGER NOT NULL,
                    object_name VARCHAR(500) NOT NULL,
                    original_name VARCHAR(500) NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    mime_type VARCHAR(100),
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(deck_id) REFERENCES decks(id)
                )
            """))
            conn.commit()
            
        yield flask_app
        
        # Полная очистка состояния после завершения теста
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    # Имитирует браузер (клиента) для отправки HTTP-запросов к нашему API
    return app.test_client()

@pytest.fixture
def runner(app):
    # Утилита для тестирования командной строки Flask
    return app.test_cli_runner()

@pytest.fixture
def test_user(client):
    # Автоматически регистрирует обычного тестового пользователя в БД
    from models import db, User
    import werkzeug.security as ws
    with flask_app.app_context():
        user = User(
            username='testuser', 
            email='testuser@example.com', 
            password_hash=ws.generate_password_hash('testpassword'),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpassword', 'id': user.id}

@pytest.fixture
def auth_headers(client, test_user):
    # Авторизует тестового юзера и возвращает заголовки с Access Token
    response = client.post('/api/auth/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_user(client):
    # Создает аккаунт с правами администратора
    from models import db, User
    import werkzeug.security as ws
    with flask_app.app_context():
        admin = User(
            username='adminuser', 
            email='admin@example.com', 
            password_hash=ws.generate_password_hash('adminpassword'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        return {'username': 'adminuser', 'email': 'admin@example.com', 'password': 'adminpassword', 'id': admin.id}

@pytest.fixture
def admin_headers(client, admin_user):
    # Авторизует админа и возвращает токен доступа
    response = client.post('/api/auth/login', json={
        'username': admin_user['username'],
        'password': admin_user['password']
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
