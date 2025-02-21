from app import db
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    status = db.Column(db.String(20), default='in_progress')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Bidirectional relationships to both User and Resource
    user = db.relationship('User', back_populates='applications')
    resource = db.relationship('Resource', back_populates='applications')
    todos = db.relationship('Todo', back_populates='application', cascade='all, delete-orphan')
    
    def create_todos_from_tasks(self):
        """Create Todo items for each Task associated with the Resource"""
        from app.models.todo import Todo
        
        for task in self.resource.tasks:
            todo = Todo(
                application_id=self.id,
                task_id=task.id,
                due_date=task.due_date
            )
            db.session.add(todo) 