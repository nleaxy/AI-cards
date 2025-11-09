import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///study_cards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenRouter API
    API_KEY = os.environ.get('API_KEY')
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "mistralai/devstral-small-2505"