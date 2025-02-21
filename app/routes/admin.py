from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Resource
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users/<uuid:id>/make-blogger', methods=['POST'])
@login_required
def make_blogger(id):
    if not current_user.role == 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    user.role = 'blogger'
    db.session.commit()
    flash(f'User {user.username} is now a blogger.', 'success')
    return redirect(url_for('admin.users')) 


# app/routes/admin.py


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users/<uuid:id>/make-blogger', methods=['POST'])
@login_required
def make_blogger(id):
    if not current_user.role == 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    user.role = 'blogger'
    db.session.commit()
    flash(f'User {user.username} is now a blogger.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/resources/<int:id>/delete', methods=['POST'])
@login_required
def delete_resource(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Proceed with delete
    resource = Resource.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()

    flash(f'Resource \"{resource.name}\" deleted.', 'success')
    return redirect(url_for('resources.index'))


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    # If you're using environment-based admin checks:
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))

    # If you have a role-based system, you'd do:
    # if current_user.role != 'admin':
    #     flash('Unauthorized access.', 'error')
    #     return redirect(url_for('main.index'))

    return render_template('admin/dashboard.html')

# (the rest of your admin routes...)


import logging
from app.models.user import User, Role
from app import db
from supabase import create_client, Client
from app.config import Config

def ensure_admin_users():
    """Ensure all emails in ADMIN_EMAILS exist and have the 'admin' role."""
    # Connect to Supabase
    supabase: Client = create_client(
        Config.SUPABASE_URL,
        Config.SUPABASE_ANON_KEY
    )
    
    # Ensure "admin" Role object is created
    admin_role, _ = Role.get_or_create(name="admin", description="Administrator role with full privileges")
    
    for email in Config.ADMIN_EMAILS:
        user = User.query.filter_by(email=email).first()
        
        # 1) If user doesn't exist, create them in Supabase and locally
        if not user:
            try:
                print("Creating user in Supabase")
                auth_response = supabase.auth.admin.create_user({
                    "email": email,
                    "password": "TempPassword123!"
                })
                if auth_response.user:
                    user = User(
                        email=email,
                    )
                    user.set_password("TempPassword123!")
                    # add to DB
                    db.session.add(user)
                    db.session.commit()
                    logging.info(f"Created user record for {email}")
                else:
                    logging.error(f"Failed to create Supabase user for: {email}")
                    continue  # move on to next email
            except Exception as e:
                logging.error(f"Error creating admin user {email}: {str(e)}")
                continue
        
        # 2) If user exists but doesn't have the admin role, assign it
        if not user.has_role("admin"):
            user.roles.append(admin_role)
            db.session.commit()
            logging.info(f"Assigned 'admin' role to {email}")