from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from supabase import create_client
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
supabase = None

def init_supabase():
    global supabase
    # Debug logging
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    logging.info(f"Initializing Supabase with URL: {supabase_url}")
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Missing Supabase configuration. "
            "Please check SUPABASE_URL and SUPABASE_ANON_KEY in your .env file."
        )
    
    supabase = create_client(
        supabase_url,
        supabase_key
    ) 