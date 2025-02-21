from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Resource, Tag, Task, Todo, Application
from app import db
import csv
from io import StringIO
from datetime import datetime
from flask import current_app
from app.utils.decorators import admin_required

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/resources')
def index():
    resources = Resource.query.all()
    return render_template('resources/index.html', 
                         resources=resources,
                         now=datetime.utcnow())

@resources_bp.route('/resources/<int:id>')
def show(id):
    resource = Resource.query.get_or_404(id)
    return render_template('resources/show.html', resource=resource)

@resources_bp.route('/resources/<int:id>/star', methods=['POST'])
@login_required
def star(id):
    resource = Resource.query.get_or_404(id)
    if current_user.has_starred(resource):
        flash('You have already starred this resource.', 'warning')
    else:
        application = current_user.star_resource(resource)
        db.session.commit()
        flash('Resource starred successfully!', 'success')
    return redirect(url_for('resources.show', id=id))

def process_csv(file_content, resource_type):
    """Process CSV content and create resources with tags"""
    csv_file = StringIO(file_content.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    # Get resource type configuration
    type_config = current_app.config['RESOURCE_TYPES'].get(resource_type)
    if not type_config:
        flash(f'Invalid resource type: {resource_type}', 'error')
        return False
    
    # Create resource type tag
    type_tag = Tag.query.filter_by(name=resource_type).first()
    if not type_tag:
        type_tag = Tag(name=resource_type)
        db.session.add(type_tag)
    
    resources_created = 0
    for row in reader:
        try:
            if not row.get('name'):
                continue
                
            # Create resource with common fields
            resource = Resource(
                name=row['name'],
                description=row.get('description', ''),
                deadline=datetime.strptime(row['deadline'], '%m/%d/%y') if row.get('deadline') else None,
                apply_link=row.get('apply_link', ''),
                resource_type=resource_type
            )
            
            # Add type-specific attributes
            attributes = {}
            for field_key in type_config['fields'].keys():
                if field_key in row:
                    attributes[field_key] = row[field_key]
            resource.attributes = attributes
            
            # Add tags
            resource.tags.append(type_tag)  # Add resource type as tag
            if row.get('tags'):
                tag_names = [t.strip() for t in row['tags'].split(',')]
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    resource.tags.append(tag)
            
            # Add default tasks for this resource type
            for task_name in type_config['tasks']:
                task = Task(
                    name=task_name,
                    resource=resource
                )
                db.session.add(task)
            
            db.session.add(resource)
            resources_created += 1
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing row: {str(e)}', 'error')
            return False
    
    try:
        db.session.commit()
        return resources_created
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving to database: {str(e)}', 'error')
        return False

@resources_bp.route('/resources/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_resources():
    if request.method == 'POST':
        resource_type = request.form.get('resource_type')
        file = request.files.get('file')
        
        if file and file.filename.endswith('.csv'):
            result = process_csv(file.read(), resource_type)
            if result:
                flash(f'Successfully imported {result} resources', 'success')
            return redirect(url_for('admin.manage_resources'))
        
        flash('Invalid file type. Please upload a CSV file.', 'error')
        return redirect(url_for('admin.manage_resources'))
    
    flash('Invalid request method', 'error')
    return redirect(url_for('admin.manage_resources'))

@resources_bp.route('/todos/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_todo(id):
    todo = Todo.query.get_or_404(id)
    # Ensure the todo belongs to the current user
    if todo.application.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    todo.status = 'completed' if todo.status != 'completed' else 'not_started'
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'todo_status': todo.status
    })

@resources_bp.route('/todos/create', methods=['POST'])
@login_required
def create_todo():
    data = request.get_json()
    
    # Get the application and verify ownership
    application = Application.query.get_or_404(data['application_id'])
    if application.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Create a new task for this todo
    task = Task(
        name=data['name'],
        resource=application.resource
    )
    db.session.add(task)
    
    # Create the todo
    todo = Todo(
        task=task,
        application=application,
        status='not_started'
    )
    if data.get('due_date'):
        todo.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
    
    db.session.add(todo)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'todo': {
                'id': todo.id,
                'name': task.name,
                'status': todo.status,
                'due_date': todo.due_date.strftime('%Y-%m-%d') if todo.due_date else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500 