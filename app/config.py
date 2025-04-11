import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supabase configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # TinyMCE configuration
    TINYMCE_API_KEY = os.getenv('TINYMCE_API_KEY')
    
    # Admin configuration
    ADMIN_EMAILS = ['angelv4331@gmail.com', 'Vincent.dangelo@gilmour.org']
    
    # Resource type configurations
    RESOURCE_TYPES = {
        'scholarship': {
            'display_name': 'Scholarship',
            'fields': {
                'amount': 'Amount',
                'open_date': 'Open Date'
            },
            'tasks': [
                "Review eligibility requirements",
                "Gather required documents",
                "Write required essays",
                "Request recommendation letters",
                "Submit application"
            ]
        },
        'fly-in': {
            'display_name': 'Fly-In Program',
            'fields': {
                'location': 'Location',
                'dates': 'Program Dates',
                'travel_covered': 'Travel Coverage',
                'housing': 'Housing Details'
            },
            'tasks': [
                "Check eligibility",
                "Gather required documents",
                "Request recommendation letters",
                "Plan travel arrangements",
                "Submit application"
            ]
        },
        'pre-college': {
            'display_name': 'Pre-College Program',
            'fields': {
                'duration': 'Program Duration',
                'cost': 'Program Cost',
                'location': 'Location',
                'dates': 'Program Dates',
                'housing': 'Housing Details'
            },
            'tasks': [
                "Review program details",
                "Check costs and financial aid",
                "Gather application materials",
                "Submit application",
                "Plan travel if needed"
            ]
        }
    } 

    # Logging configuration
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    LOGGING_CONFIG = {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/access_point.log',
                'maxBytes': 10240,
                'backupCount': 10,
                'formatter': 'default',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            }
        },
        'root': {
            'level': LOG_LEVEL,
            'handlers': ['file', 'console'] if LOG_TO_STDOUT else ['file']
        }
    } 