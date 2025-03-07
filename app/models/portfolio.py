from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"

class CollegeApplication(db.Model):
    __tablename__ = 'college_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    college_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default=ApplicationStatus.APPLIED)
    scholarships_awarded = db.Column(db.Text)
    honors_program = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='college_applications')
    essays = db.relationship('Essay', back_populates='college_application', cascade='all, delete-orphan')

class Essay(db.Model):
    __tablename__ = 'essays'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    college_application_id = db.Column(db.Integer, db.ForeignKey('college_applications.id'))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='essays')
    college_application = db.relationship('CollegeApplication', back_populates='essays')

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, unique=True)
    bio_card = db.Column(db.Text)
    intended_major = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='portfolio') 