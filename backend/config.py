import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///study_cards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys and URLs
    API_KEY = os.environ.get('API_KEY') or os.environ.get('GEMINI_API_KEY')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'dev-jwt-secret-key-change-in-production'

    # MinIO
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'uploads')
    JWT_ACCESS_TOKEN_EXPIRES = False  # Tokens never expire (for development)
    
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "mistralai/devstral-small-2505"