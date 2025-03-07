from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Application, BlogPost
from datetime import datetime
from bs4 import BeautifulSoup
import html

main_bp = Blueprint('main', __name__)

def clean_html_content(content):
    """Clean HTML content and return plain text"""
    if not content:
        return ""
    # Decode HTML entities
    content = html.unescape(content)
    # Remove HTML tags
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text(separator=' ').strip()

@main_bp.route('/')
def index():
    recent_posts = BlogPost.query.filter_by(status='published')\
        .order_by(BlogPost.published_at.desc())\
        .limit(2)\
        .all()
    
    # Clean the titles and content for each post
    for post in recent_posts:
        post.clean_title = clean_html_content(post.title)
        post.clean_excerpt = clean_html_content(post.content)[:150] + "..."
    
    return render_template('main/index.html', recent_posts=recent_posts)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's applications (starred resources) with related tasks
    applications = Application.query.filter_by(user_id=current_user.id)\
        .order_by(Application.created_at.desc()).all()
    
    # Calculate completed tasks
    completed_tasks = sum(
        1 for app in applications 
        for todo in app.todos 
        if todo.status == 'completed'
    )
    
    # Add current datetime for deadline comparisons
    now = datetime.utcnow()
    
    return render_template('main/dashboard.html', 
                         applications=applications,
                         completed_tasks=completed_tasks,
                         now=now)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')

@main_bp.route('/justin-is-awesome')
def justin_plaque():
    """Easter egg route for Justin's wall of fame"""
    return render_template('justin_plaque.html') 