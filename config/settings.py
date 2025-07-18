import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    
    # Supabase PostgreSQL configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    # Database URI - use Supabase if available, fallback to DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL')
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "echo": False
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration for Replit
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_FILE_DIR = './flask_session'
    SESSION_FILE_THRESHOLD = 500
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Allow both HTTP and HTTPS for development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None  # Auto-detect domain
    
    # Trading configuration
    AUTO_REFRESH_INTERVAL = 30  # seconds
    MAX_API_RETRIES = 3
    API_TIMEOUT = 30  # seconds
    
    # Replit deployment configuration
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'https'
    SERVER_NAME = None  # Allow any host

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'

# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name.get(env, DevelopmentConfig)