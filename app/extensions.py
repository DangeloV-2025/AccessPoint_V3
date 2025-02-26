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
    
    logging.info(f"Initializing Supabase...")
    logging.info(f"URL found: {'Yes' if supabase_url else 'No'}")
    logging.info(f"Key found: {'Yes' if supabase_key else 'No'}")
    
    if not supabase_url or not supabase_key:
        available_env = {k: v for k, v in os.environ.items() if 'SUPABASE' in k}
        logging.error(f"Available Supabase environment variables: {available_env}")
        raise RuntimeError(
            "Missing Supabase configuration. "
            "Please check SUPABASE_URL and SUPABASE_ANON_KEY in your .env file."
        )
    
    try:
        supabase = create_client(
            supabase_url,
            supabase_key
        )
        logging.info("Supabase client initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing Supabase client: {str(e)}")
        raise

    return supabase 