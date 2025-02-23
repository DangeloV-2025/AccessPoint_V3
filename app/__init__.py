from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, init_supabase
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/access_point.log', 
                                     maxBytes=10240, 
                                     backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Access Point startup')
    
    # Verify required config
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError(
            'DATABASE_URL environment variable is not set. '
            'Please check your .env file and environment variables.'
        )
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    init_supabase()  # No need to pass app anymore
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.resources import resources_bp
    from app.routes.blog import blog_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(blog_bp)
    
    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)
    
    return app
