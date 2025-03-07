from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, init_supabase
import logging
from logging.handlers import RotatingFileHandler
import os
import click
from flask_migrate import Migrate

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
    migrate = Migrate()
    migrate.init_app(app, db)
    login_manager.init_app(app)
    init_supabase()  # No need to pass app anymore
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.resources import resources_bp
    from app.routes.blog import blog_bp
    from app.routes.portfolio import portfolio_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(portfolio_bp)
    
    # Register CLI commands
    register_commands(app)
    
    # Register template context processors
    from app.utils.helpers import get_pending_blog_count
    
    @app.context_processor
    def utility_processor():
        return {
            'get_pending_blog_count': get_pending_blog_count
        }
    
    return app

def register_commands(app):
    """Register custom Flask CLI commands."""
    
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo("Initialized the database.")
    
    @app.cli.command("migrate-blog")
    def migrate_blog():
        """Run blog migration to add review fields."""
        from migrations.add_blog_review_fields import run_migration
        run_migration()
        click.echo("Blog migration completed.")
    
    @app.cli.command("create-admin")
    def create_admin():
        """Create admin users from config."""
        from app.routes.admin import ensure_admin_users
        ensure_admin_users()
        click.echo("Admin users created.")
        
    @app.cli.command("process-blog-queue")
    def process_blog_queue():
        """Process pending blog posts in the queue."""
        from app.routes.admin import process_pending_posts
        count = process_pending_posts()
        click.echo(f"Processed {count} pending blog posts.")
