from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Resource, BlogPost, Role, BlogCategory, Tag
from app import db
from werkzeug.utils import secure_filename
import csv
from io import StringIO
from datetime import datetime
import os

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

@admin_bp.route('/admin/resources/import', methods=['GET', 'POST'])
@login_required
def import_resources():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))

    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        resource_type = request.form.get('resource_type')
        
        if not file or not resource_type:
            flash('Missing required fields', 'error')
            return redirect(request.url)

        try:
            # Read CSV file
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = csv.DictReader(stream)
            rows_processed = 0
            errors = []
            
            for row in csv_data:
                try:
                    # Basic validation
                    # Handle program_name field for fly-ins
                    if row.get('program_name'):
                        row['name'] = row['program_name']
                    
                    if not row.get('name'):
                        errors.append(f"Row {rows_processed + 1}: Missing name field")
                        continue

                    # Create base resource
                    resource = Resource(
                        name=row.get('name'),
                        description=row.get('description') or row.get('target_applicants'),  # Use target_applicants as description for fly-ins
                        resource_type=resource_type,
                        apply_link=row.get('apply_link')
                    )

                    # Handle deadline based on resource type
                    deadline_str = None
                    if resource_type == 'fly-in':
                        deadline_str = row.get('regular_deadline')
                    else:
                        deadline_str = row.get('deadline')

                    if deadline_str and deadline_str.lower() not in ['nan', 'rolling', 'not offered for 2025']:
                        try:
                            # Try different date formats
                            date_formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y']
                            for fmt in date_formats:
                                try:
                                    resource.deadline = datetime.strptime(deadline_str.strip(), fmt)
                                    break
                                except ValueError:
                                    continue
                            if not resource.deadline and deadline_str:
                                errors.append(f"Row {rows_processed + 1}: Invalid date format - {deadline_str}")
                        except Exception as e:
                            errors.append(f"Row {rows_processed + 1}: Date error - {str(e)}")

                    # Handle type-specific fields
                    attributes = {}
                    if resource_type == 'fly-in':
                        attributes.update({
                            'host_institution': row.get('host_institution'),
                            'program_name': row.get('program_name'),
                            'in_person': row.get('in_person', True),
                            'email': row.get('email'),
                            'priority_deadline': row.get('priority_deadline'),
                            'regular_deadline': row.get('regular_deadline'),
                            'target_applicants': row.get('target_applicants'),
                            'session_1': row.get('session_1'),
                            'session_2': row.get('session_2'),
                            'session_3': row.get('session_3'),
                            'num_essays': row.get('num_essays'),
                            'num_lors': row.get('num_LORs'),
                            'other_notes': row.get('other_notes'),
                            'hosting_situation': row.get('hosting_situation'),
                            'program_status': row.get('program_status', 'TRUE') == 'TRUE'
                        })
                    elif resource_type == 'scholarship':
                        attributes.update({
                            'amount': row.get('amount'),
                            'open_date': row.get('open_date')
                        })
                    elif resource_type == 'pre-college':
                        attributes.update({
                            'organization': row.get('organization'),
                            'grade_eligibility': row.get('grade_eligibility')
                        })

                    resource.attributes = {k: v for k, v in attributes.items() if v is not None}

                    # Handle tags
                    if row.get('tags'):
                        tag_names = [t.strip() for t in row['tags'].split(',') if t.strip()]
                        for tag_name in tag_names:
                            tag = Tag.query.filter_by(name=tag_name).first()
                            if not tag:
                                tag = Tag(name=tag_name)
                                db.session.add(tag)
                            resource.tags.append(tag)

                    db.session.add(resource)
                    rows_processed += 1

                except Exception as e:
                    errors.append(f"Row {rows_processed + 1}: {str(e)}")
                    current_app.logger.error(f"Error processing row {rows_processed + 1}: {str(e)}")
                    continue

            db.session.commit()
            
            # Show success/error messages
            if rows_processed > 0:
                flash(f'Successfully imported {rows_processed} resources', 'success')
            if errors:
                for error in errors:
                    flash(error, 'error')
                current_app.logger.error(f"Import errors: {errors}")

        except Exception as e:
            db.session.rollback()
            flash(f'Error importing resources: {str(e)}', 'error')
            current_app.logger.error(f"Import error: {str(e)}")
            
    return render_template('admin/import_resources.html')

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