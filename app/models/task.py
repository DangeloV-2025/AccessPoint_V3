from app import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resource = db.relationship('Resource', back_populates='tasks')
    todos = db.relationship('Todo', back_populates='task', cascade='all, delete-orphan') 