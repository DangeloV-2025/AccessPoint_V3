from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging
from flask import current_app

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
supabase = None

def init_supabase(app: Flask) -> None:
    """Initialize Supabase client with app context"""
    global supabase
    
    supabase_url = app.config.get('SUPABASE_URL')
    supabase_key = app.config.get('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be configured")
        
    supabase = create_client(supabase_url, supabase_key)

    return supabase 