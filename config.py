import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application Security & Configuration Settings."""
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if FLASK_ENV == 'production':
            raise RuntimeError("CRITICAL SECURITY ERROR: 'SECRET_KEY' environment variable must be set in production mode!")
        else:
            SECRET_KEY = 'smart-ai-doctor-dev-only-secret-key-change-in-production'
    
    # OpenAI API Key (Loaded strictly from environment)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
    
    # SQLite Database Path
    DATABASE_PATH = os.path.join(BASE_DIR, 'smart_doctor.db')
    
    # Model & Data Paths
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Ensure data and models directories exist
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.MODELS_DIR, exist_ok=True)
