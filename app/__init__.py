from flask import Flask
from app.config import Config
from app.extensions import db, login_manager
import logging

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
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
