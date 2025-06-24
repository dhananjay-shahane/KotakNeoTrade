"""
Render-optimized entry point for Kotak Neo Trading Application
Production-ready deployment configuration
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_production_environment():
    """Setup production environment configuration"""
    # Production environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Create necessary directories
    os.makedirs('flask_session', exist_ok=True)
    
    logger.info("Production environment configured")

# Setup environment
setup_production_environment()

# Import the main Flask app
from app import app

# Production configuration
app.config.update(
    DEBUG=False,
    TESTING=False,
    ENV='production',
    # Session configuration for production
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
    # Security settings
    SESSION_COOKIE_SECURE=True if os.environ.get('ENVIRONMENT') == 'production' else False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Initialize database for production
def init_database():
    """Initialize database tables for production"""
    with app.app_context():
        try:
            from app import db
            
            # Import all models to ensure they're registered
            import models
            import models_etf
            
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Verify database connection
            db.session.execute('SELECT 1')
            db.session.commit()
            logger.info("Database connection verified")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            sys.exit(1)

# Initialize database on startup
init_database()

# For Render deployment
application = app

# Health check endpoint
@app.route('/render-health')
def render_health():
    """Render-specific health check"""
    try:
        from app import db
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)