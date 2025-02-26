"""
Migration script to add review_notes field to blog_posts table
"""
from app import db, create_app
from sqlalchemy import Column, Text, String, DateTime
from sqlalchemy.sql import text

def run_migration():
    app = create_app()
    with app.app_context():
        # Check if the column already exists
        conn = db.engine.connect()
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('blog_posts')]
        
        # Add review_notes column if it doesn't exist
        if 'review_notes' not in columns:
            print("Adding review_notes column to blog_posts table...")
            conn.execute(text("ALTER TABLE blog_posts ADD COLUMN review_notes TEXT;"))
            conn.commit()
            print("Added review_notes column successfully.")
        else:
            print("review_notes column already exists.")
        
        # Make sure status column has the right values
        print("Updating status values in blog_posts table...")
        # Update any NULL status values to 'draft'
        conn.execute(text("UPDATE blog_posts SET status = 'draft' WHERE status IS NULL;"))
        # Set all existing published posts to have the right status
        conn.execute(text("UPDATE blog_posts SET status = 'published' WHERE published_at IS NOT NULL AND status != 'pending_review';"))
        conn.commit()
        print("Status values updated successfully.")
        
        conn.close()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration() 