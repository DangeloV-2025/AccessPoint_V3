from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from flask import current_app

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
supabase = None

def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase_url = current_app.config['SUPABASE_URL']
        supabase_key = current_app.config['SUPABASE_ANON_KEY']
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL and key must be configured")
            
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        current_app.logger.error(f"Supabase initialization error: {str(e)}")
        raise

    return supabase 