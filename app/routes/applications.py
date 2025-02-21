from flask import Blueprint

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/applications')
def index():
    return "Applications index" 