from app.extensions import db
from datetime import datetime
from .tag import resource_tags
from sqlalchemy.dialects.postgresql import JSONB

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    apply_link = db.Column(db.String(500))
    resource_type = db.Column(db.String(50), nullable=False)  # Should contain 'scholarship', 'fly-in', or 'pre-college'
    attributes = db.Column(JSONB)  # Store type-specific fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('Tag',
                          secondary=resource_tags,
                          back_populates='resources')
    tasks = db.relationship('Task', back_populates='resource', cascade='all, delete-orphan')
    applications = db.relationship('Application', back_populates='resource', cascade='all, delete-orphan')
    
    def starred_by(self, user):
        """Check if resource is starred by specific user"""
        return Application.query.filter_by(
            user_id=user.id,
            resource_id=self.id
        ).first() is not None 