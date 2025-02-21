import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost/college_access_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
    

    # Add this new config value
    ADMIN_EMAILS = [
        email.strip()
        for email in os.environ.get("ADMIN_EMAILS", "").split(",")
        if email.strip()
    ]
    
    

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