from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Resource, BlogPost, Role, BlogCategory, Tag
from app import db
from werkzeug.utils import secure_filename
import csv
from io import StringIO
from datetime import datetime
import os
from supabase import create_client, Client
from app.utils.decorators import admin_required

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
def assign_role(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(id)
    role_name = request.form.get('role')
    
    if not role_name:
        flash('No role selected.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        flash(f'Role {role_name} not found.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        flash(f'Role {role_name} assigned to {user.email}.', 'success')
    else:
        flash(f'User already has the role {role_name}.', 'info')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/users/<uuid:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Prevent admins from deleting themselves
    if current_user.id == id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user = User.query.get_or_404(id)
    
    try:
        # Store email for the success message
        user_email = user.email
        
        # Delete user's applications and related data
        applications = user.applications
        for app in applications:
            db.session.delete(app)
        
        # Delete user's blog posts
        blog_posts = user.blog_posts
        for post in blog_posts:
            db.session.delete(post)
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        # Try to delete the user from Supabase as well
        try:
            supabase_admin_client = create_client(
                current_app.config['SUPABASE_URL'],
                current_app.config['SUPABASE_SERVICE_KEY']
            )
            supabase_admin_client.auth.admin.delete_user(str(id))
            current_app.logger.info(f"Deleted user {user_email} from Supabase")
        except Exception as e:
            current_app.logger.error(f"Failed to delete user from Supabase: {str(e)}")
            # Continue even if Supabase deletion fails
        
        flash(f'User {user_email} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        flash(f'Error deleting user: {str(e)}', 'error')
    
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

@admin_bp.route('/admin/blogs/<int:id>/delete', methods=['POST'])
@login_required
def delete_blog_post(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        post = BlogPost.query.get_or_404(id)
        db.session.delete(post)
        db.session.commit()
        flash('Blog post deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting blog post: {str(e)}")
        flash('Error deleting blog post.', 'error')
    
    return redirect(url_for('admin.manage_blogs'))

@admin_bp.route('/admin/blog-queue')
@login_required
@admin_required
def blog_queue():
    pending_posts = BlogPost.query.filter_by(status='pending').order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog_queue.html', posts=pending_posts)

@admin_bp.route('/admin/blog/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_blog(id):
    post = BlogPost.query.get_or_404(id)
    post.publish()  # This sets status to published and sets published_at
    db.session.commit()
    
    flash(f'Blog post "{post.title}" has been published.', 'success')
    return redirect(url_for('admin.blog_queue'))

@admin_bp.route('/admin/blog/<int:id>/reject', methods=['POST'])
@login_required
def reject_blog(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    post = BlogPost.query.get_or_404(id)
    notes = request.form.get('notes')
    
    post.status = 'rejected'
    post.review_notes = notes
    db.session.commit()
    
    flash(f'Blog post "{post.title}" has been rejected.', 'success')
    return redirect(url_for('admin.blog_queue'))

@admin_bp.route('/admin/blog-management')
@login_required
def blog_management():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Get both published and draft posts
    published_posts = BlogPost.query.filter_by(status='published')\
        .order_by(BlogPost.published_at.desc()).all()
    draft_posts = BlogPost.query.filter_by(status='draft')\
        .order_by(BlogPost.created_at.desc()).all()
    
    return render_template('admin/blog_management.html',
                         published_posts=published_posts,
                         draft_posts=draft_posts)

@admin_bp.route('/admin/db-health')
@login_required
def check_db_health():
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Get all models from SQLAlchemy
        models = db.Model.__subclasses__()
        tables = db.engine.table_names()
        
        # Compare model tables with actual database tables
        model_tables = {model.__tablename__ for model in models}
        missing_tables = model_tables - set(tables)
        extra_tables = set(tables) - model_tables
        
        health_data = {
            'status': 'healthy',
            'database_connected': True,
            'models_count': len(models),
            'database_tables_count': len(tables),
            'missing_tables': list(missing_tables),
            'extra_tables': list(extra_tables),
            'is_synced': len(missing_tables) == 0 and len(extra_tables) == 0,
            'models': [model.__tablename__ for model in models],
            'tables': tables
        }
        
        return render_template('admin/db_health.html', health_data=health_data)
        
    except Exception as e:
        health_data = {
            'status': 'unhealthy',
            'error': str(e)
        }
        return render_template('admin/db_health.html', health_data=health_data), 500

@admin_bp.route("/blog/review/<int:post_id>/<action>", methods=["POST"])
@login_required
@admin_required
def review_blog_post(post_id, action):
    post = BlogPost.query.get_or_404(post_id)
    
    if action not in ['approve', 'reject']:
        flash('Invalid action', 'error')
        return redirect(url_for('admin.blog_queue'))
    
    try:
        post.status = 'published' if action == 'approve' else 'rejected'
        post.reviewed_by = current_user.id
        post.reviewed_at = datetime.utcnow()
        post.review_notes = request.form.get('notes', '')
        
        db.session.commit()
        
        flash(f'Blog post has been {action}ed', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during review', 'error')
    
    return redirect(url_for('admin.blog_queue'))