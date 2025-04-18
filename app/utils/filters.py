from datetime import datetime

def format_datetime(value):
    """Format a datetime object to a readable string"""
    if value is None:
        return ""
    return value.strftime('%B %d, %Y at %I:%M %p') 