from app.models import BlogPost

def get_pending_blog_count():
    """Get the count of blog posts pending review"""
    return BlogPost.query.filter_by(status='pending_review').count() 