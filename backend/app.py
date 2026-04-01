from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint

from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)

# включаем cors с поддержкой куки - без этого браузер не будет отправлять httponly cookie на другой домен
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Study Cards API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Create tables and run migrations inside app context
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE decks ADD COLUMN emoji VARCHAR(10)"))
            conn.commit()
            print("Added emoji column to decks table")
    except Exception:
        pass  # Column likely already exists

    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
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
            conn.commit()
            print("Ensured refresh_tokens table exists")
    except Exception as e:
        print(f"Error checking refresh_tokens table: {e}")

# Register Blueprints (API layer)
from api.auth_routes import auth_bp
from api.admin_routes import admin_bp
from api.deck_routes import deck_bp
from api.stats_routes import stats_bp
from api.main_routes import main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(deck_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(main_bp)


# Swagger JSON spec endpoint
@app.route('/api/swagger.json')
def swagger_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Study Cards API",
            "description": "API для создания учебных карточек из PDF с использованием AI",
            "version": "2.0.0"
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
                        "role": {"type": "string", "enum": ["user", "admin"]},
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
                    "summary": "Health check",
                    "responses": {"200": {"description": "API is running"}}
                }
            },
            "/api/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register a new user",
                    "responses": {
                        "201": {"description": "User registered"},
                        "400": {"description": "Validation error"}
                    }
                }
            },
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login",
                    "responses": {
                        "200": {"description": "Successful login"},
                        "401": {"description": "Invalid credentials"}
                    }
                }
            },
            "/api/auth/refresh": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Refresh access token",
                    "responses": {
                        "200": {"description": "New tokens"},
                        "401": {"description": "Invalid refresh token"}
                    }
                }
            },
            "/api/auth/logout": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Logout and revoke refresh token",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Logged out"}}
                }
            },
            "/api/admin/users": {
                "get": {
                    "tags": ["Admin"],
                    "summary": "List all users (admin only)",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "User list"},
                        "403": {"description": "Forbidden"}
                    }
                }
            },
            "/api/admin/users/{user_id}/role": {
                "put": {
                    "tags": ["Admin"],
                    "summary": "Update user role (admin only)",
                    "security": [{"bearerAuth": []}],
                    "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"description": "Role updated"},
                        "403": {"description": "Forbidden"}
                    }
                }
            },
            "/api/decks": {
                "get": {
                    "tags": ["Decks"],
                    "summary": "Get user decks",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Deck list"}, "401": {"description": "Unauthorized"}}
                }
            },
            "/api/decks/{deck_id}": {
                "get": {
                    "tags": ["Decks"],
                    "summary": "Get deck with cards",
                    "parameters": [{"name": "deck_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Deck details"}, "404": {"description": "Not found"}}
                },
                "put": {
                    "tags": ["Decks"],
                    "summary": "Update deck",
                    "security": [{"bearerAuth": []}],
                    "parameters": [{"name": "deck_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Deck updated"}}
                },
                "delete": {
                    "tags": ["Decks"],
                    "summary": "Delete deck",
                    "parameters": [{"name": "deck_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Deck deleted"}}
                }
            },
            "/api/stats": {
                "get": {
                    "tags": ["Statistics"],
                    "summary": "Get user statistics",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "User stats"}, "401": {"description": "Unauthorized"}}
                }
            },
            "/api/stats/reset": {
                "post": {
                    "tags": ["Statistics"],
                    "summary": "Reset user statistics",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Stats reset"}}
                }
            },
            "/api/sessions": {
                "post": {
                    "tags": ["Study"],
                    "summary": "Save study session",
                    "security": [{"bearerAuth": []}],
                    "responses": {"201": {"description": "Session saved"}, "401": {"description": "Unauthorized"}}
                }
            },
            "/api/upload": {
                "post": {
                    "tags": ["Decks"],
                    "summary": "Upload PDF and generate cards",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Cards generated"}, "400": {"description": "Invalid file"}}
                }
            }
        }
    }
    return jsonify(spec)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
