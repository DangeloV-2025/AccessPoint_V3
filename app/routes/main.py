from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Application
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html')

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