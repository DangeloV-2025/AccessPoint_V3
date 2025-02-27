"""
Migration script to add review_notes field to blog_posts table
"""
from app.extensions import db
from sqlalchemy import text

def run_migration():
    """Add status field to blog posts table."""
    
    with db.engine.connect() as conn:
        # Add status column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE blog_posts 
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft'
        """))
        
        # Set existing posts to published
        conn.execute(text("""
            UPDATE blog_posts 
            SET status = 'published' 
            WHERE status IS NULL
        """))
        
        conn.commit()

if __name__ == "__main__":
    run_migration() 