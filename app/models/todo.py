from app import db
from datetime import datetime

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    due_date = db.Column(db.DateTime)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    user_notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', back_populates='todos')
    application = db.relationship('Application', back_populates='todos')
    
    def mark_complete(self):
        self.status = 'completed'
        self.completed_at = datetime.utcnow() 