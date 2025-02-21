from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, published
    category_id = db.Column(db.Integer, db.ForeignKey('blog_categories.id'))
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    author = db.relationship('User', back_populates='blog_posts')
    category = db.relationship('BlogCategory', back_populates='posts')
    
    def publish(self):
        self.status = 'published'
        self.published_at = datetime.utcnow() 