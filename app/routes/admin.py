from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Resource, BlogPost, Role, BlogCategory
from app import db
from werkzeug.utils import secure_filename
import csv
from io import StringIO
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    users_count = User.query.count()
    resources_count = Resource.query.count()
    blog_posts_count = BlogPost.query.count()
    
    return render_template('admin/dashboard.html',
                         users_count=users_count,
                         resources_count=resources_count,
                         blog_posts_count=blog_posts_count)

# User Management
@admin_bp.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)

@admin_bp.route('/admin/roles/new', methods=['POST'])
@login_required
def create_role():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if Role.query.filter_by(name=name).first():
        flash('Role already exists.', 'error')
    else:
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        flash('Role created successfully!', 'success')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/users/<uuid:id>/role', methods=['POST'])
@login_required
def update_user_role(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    role_name = request.form.get('role')
    role = Role.query.filter_by(name=role_name).first()
    
    if role:
        user.roles = [role]  # Replace existing roles
        db.session.commit()
        flash(f'Updated role for {user.email}', 'success')
    
    return redirect(url_for('admin.manage_users'))

# Resource Management
@admin_bp.route('/admin/resources')
@login_required
def manage_resources():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    resources = Resource.query.all()
    return render_template('admin/resources.html', resources=resources)

@admin_bp.route('/admin/resources/import', methods=['POST'])
@login_required
def import_resources():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))

    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin.manage_resources'))

    file = request.files['file']
    resource_type = request.form.get('resource_type')

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.manage_resources'))

    if not resource_type:
        flash('Resource type is required', 'error')
        return redirect(url_for('admin.manage_resources'))

    if file and file.filename.endswith('.csv'):
        try:
            # Read and process CSV
            csv_content = file.read().decode('utf-8')
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            resources_created = 0
            for row in reader:
                try:
                    # Create resource
                    resource = Resource(
                        name=row.get('name'),
                        description=row.get('description', ''),
                        resource_type=resource_type,
                        apply_link=row.get('apply_link', ''),
                        deadline=datetime.strptime(row['deadline'], '%m/%d/%y') if row.get('deadline') else None
                    )
                    
                    # Add type-specific attributes
                    attributes = {}
                    type_config = current_app.config['RESOURCE_TYPES'].get(resource_type, {})
                    for field_key in type_config.get('fields', {}).keys():
                        if field_key in row:
                            attributes[field_key] = row[field_key]
                    resource.attributes = attributes
                    
                    db.session.add(resource)
                    resources_created += 1
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error processing row: {str(e)}', 'error')
                    return redirect(url_for('admin.manage_resources'))
            
            db.session.commit()
            flash(f'Successfully imported {resources_created} resources', 'success')
            
        except Exception as e:
            flash(f'Error processing CSV: {str(e)}', 'error')
            return redirect(url_for('admin.manage_resources'))
    else:
        flash('Invalid file type. Please upload a CSV file.', 'error')
    
    return redirect(url_for('admin.manage_resources'))

@admin_bp.route('/admin/resources/<int:id>/delete', methods=['POST'])
@login_required
def delete_resource(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    resource = Resource.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted successfully!', 'success')
    return redirect(url_for('admin.manage_resources'))

# Blog Management
@admin_bp.route('/admin/blogs')
@login_required
def manage_blogs():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    posts = BlogPost.query.all()
    categories = BlogCategory.query.all()
    return render_template('admin/blogs.html', posts=posts, categories=categories)

@admin_bp.route('/admin/check')
@login_required
def check_admin():
    """Debug route to check admin status"""
    from flask import current_app
    
    return {
        'user_email': current_user.email,
        'is_admin': current_user.is_admin,
        'has_admin_role': current_user.has_role('admin'),
        'in_admin_emails': current_user.email in current_app.config['ADMIN_EMAILS'],
        'admin_emails_config': current_app.config['ADMIN_EMAILS'],
        'user_roles': [role.name for role in current_user.roles]
    }

import logging
from app.models.user import User, Role
from app import db
from supabase import create_client, Client
from app.config import Config

def ensure_admin_users():
    """Ensure all emails in ADMIN_EMAILS exist and have the 'admin' role."""
    from flask import current_app
    
    print(f"Starting admin user setup...")
    print(f"Admin emails from config: {current_app.config['ADMIN_EMAILS']}")
    
    try:
        # Connect to Supabase with service key
        supabase = create_client(
            current_app.config['SUPABASE_URL'],
            current_app.config['SUPABASE_SERVICE_KEY']
        )
        
        # Ensure "admin" Role exists
        admin_role, created = Role.get_or_create(
            name="admin",
            description="Administrator role with full privileges"
        )
        if created:
            print(f"Created new admin role")
        else:
            print(f"Using existing admin role")
        
        for email in current_app.config['ADMIN_EMAILS']:
            print(f"\nProcessing admin email: {email}")
            user = User.query.filter_by(email=email).first()
            
            if not user:
                print(f"User {email} does not exist, creating...")
                try:
                    # Create user in Supabase
                    auth_response = supabase.auth.admin.create_user({
                        "email": email,
                        "password": current_app.config.get('ADMIN_PASSWORD', 'TempPassword123!'),
                        "email_confirm": True,
                        "user_metadata": {"role": "admin"}
                    })
                    
                    if auth_response.user:
                        print(f"Created Supabase user for {email}")
                        # Create local user
                        user = User(
                            id=auth_response.user.id,
                            email=email
                        )
                        db.session.add(user)
                        db.session.commit()
                        print(f"Created local user record for {email}")
                    else:
                        print(f"Failed to create Supabase user for {email}")
                        continue
                        
                except Exception as e:
                    print(f"Error creating user {email}: {str(e)}")
                    continue
            
            # Ensure user has admin role
            if not user.has_role("admin"):
                print(f"Adding admin role to {email}")
                user.roles.append(admin_role)
                try:
                    db.session.commit()
                    print(f"Successfully added admin role to {email}")
                except Exception as e:
                    print(f"Error adding admin role: {str(e)}")
                    db.session.rollback()
            else:
                print(f"User {email} already has admin role")
                
    except Exception as e:
        print(f"Error in ensure_admin_users: {str(e)}")
        db.session.rollback()