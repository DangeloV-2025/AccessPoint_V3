from app import db

resource_tags = db.Table('resource_tags',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resources.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationship with Resource
    resources = db.relationship('Resource',
                              secondary=resource_tags,
                              back_populates='tags') 