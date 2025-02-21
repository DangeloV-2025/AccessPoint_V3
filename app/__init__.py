from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config
import logging

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.resources import resources_bp
    from app.routes.applications import applications_bp
    from app.routes.blog import blog_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp)

    # Ensure admin users exist after initializing app context
    with app.app_context():
        from app.routes.admin import ensure_admin_users
        ensure_admin_users()

    return app
