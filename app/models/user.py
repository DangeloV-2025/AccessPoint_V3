from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from .application import Application

@login_manager.user_loader
def load_user(id):
    return User.query.get(str(id))


# Association table for User and Role
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
)

class Role(db.Model):
    """Role model for user permissions."""
    __tablename__ = 'role'
    
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    

    @classmethod
    def get_or_create(cls, name, description=None):
        """
        Get an existing role or create it if it doesn't exist.
        
        Args:
            name (str): The name of the role
            description (str, optional): Description of the role
        
        Returns:
            tuple: (role, created) where role is the Role instance and 
                  created is a boolean indicating if a new role was created
        """
        role = cls.query.filter_by(name=name).first()
        if role is None:
            role = cls(name=name, description=description)
            db.session.add(role)
            db.session.commit()
            return role, True
        return role, False

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)



class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Increased length for scrypt hash
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', back_populates='user', cascade='all, delete-orphan')
    blog_posts = db.relationship('BlogPost', back_populates='author', lazy='dynamic')

    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has a specific role by name."""
        return any(r.name == role_name for r in self.roles)

    @property
    def is_admin(self):
        """Check if user has admin role or is in ADMIN_EMAILS"""
        from flask import current_app
        return self.has_role("admin") or self.email in current_app.config['ADMIN_EMAILS']

    

    def is_blogger(self):
        """Check if user has blogger role"""
        return self.has_role("blogger")

    def star_resource(self, resource):
        """Helper method to create an application (star) for a resource"""
        if not self.has_starred(resource):
            application = Application(user=self, resource=resource)
            db.session.add(application)
            application.create_todos_from_tasks()
            return application
    
    def has_starred(self, resource):
        """Check if user has already starred this resource"""
        from .application import Application
        return Application.query.filter_by(
            user_id=self.id, 
            resource_id=resource.id
        ).first() is not None 