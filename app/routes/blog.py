from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import BlogPost, User, BlogCategory, Comment
from app import db
from datetime import datetime
from app.utils.decorators import blogger_required
from flask import current_app
from bs4 import BeautifulSoup
import html
from app.utils.storage import upload_image_to_supabase
import uuid

blog_bp = Blueprint('blog', __name__)

def clean_html_content(content):
    """Clean HTML content and return plain text"""
    if not content:
        return ""
    # Decode HTML entities
    content = html.unescape(content)
    # Remove HTML tags
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text(separator=' ').strip()

@blog_bp.route('/blog')
def index():
    """Show all published blog posts - accessible to all users"""
    posts = BlogPost.query.filter_by(status='published')\
        .order_by(BlogPost.published_at.desc()).all()

    # Clean the titles and content for each post
    for post in posts:
        post.clean_title = clean_html_content(post.title)
        # Create a clean excerpt for the content
        post.clean_excerpt = clean_html_content(post.content)[:200] + "..."

    categories = BlogCategory.query.all()
    return render_template('blog/index.html', posts=posts, categories=categories)

# Shows specific categories
@blog_bp.route('/blog/category/<slug>')
def category(slug):
    """Show posts in a specific category"""
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    posts = BlogPost.query.filter_by(
        category=category,
        status='published'
    ).order_by(BlogPost.published_at.desc()).all()
    categories = BlogCategory.query.all()

    # Clean the titles and content for each post
    for post in posts:
        post.clean_title = clean_html_content(post.title)
        # Create a clean excerpt for the content
        post.clean_excerpt = clean_html_content(post.content)[:200] + "..."

    return render_template('blog/index.html',
                         posts=posts,
                         categories=categories,
                         current_category=category)
@blog_bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
@blogger_required
def new():
    """Create new blog post (bloggers and admins only)"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            author_name = request.form.get('author_name')
            image = request.files.get('image')

            # Clean the title
            title = clean_html_content(title)

            if not title or not content:
                flash('Title and content are required.', 'error')
                return render_template(
                    'blog/new.html',
                    post=None,
                    cancel_url=url_for('blog.index'),
                    submit_label="Publish Post" if current_user.is_admin else "Submit for Review"
                )

            # Handle image upload if present
            image_url = None
            if image and image.filename:
                # Generate a unique filename
                file_ext = image.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{file_ext}"
                
                # Upload to Supabase storage
                image_url = upload_image_to_supabase(image, filename)
                
                if not image_url:
                    flash('Failed to upload image. Post will be created without an image.', 'warning')

            post = BlogPost(
                title=title,
                content=content,
                author_name=author_name,
                author_id=current_user.id,
                status='published' if current_user.is_admin else 'pending',
                image_url=image_url
            )

            if current_user.is_admin:
                post.published_at = datetime.utcnow()

            db.session.add(post)
            db.session.commit()

            flash(
                'Your blog post has been published!' if current_user.is_admin
                else 'Your blog post has been submitted for review!',
                'success'
            )
            return redirect(url_for('blog.my_posts'))

        except Exception as e:
            current_app.logger.error(f"Error creating blog post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating your post. Please try again.', 'error')
            return render_template(
                'blog/new.html',
                post=None,
                cancel_url=url_for('blog.index'),
                submit_label="Publish Post" if current_user.is_admin else "Submit for Review"
            )

    return render_template(
        'blog/new.html',
        post=None,
        cancel_url=url_for('blog.index'),
        submit_label="Publish Post" if current_user.is_admin else "Submit for Review"
    )


@blog_bp.route('/blog/<int:id>')
def show(id):
    """Show a specific blog post - accessible to all users"""
    post = BlogPost.query.get_or_404(id)
    if post.status != 'published' and (not current_user.is_authenticated or
                                     not (current_user.is_admin or current_user == post.author)):
        flash('This post is not available.', 'error')
        return redirect(url_for('blog.index'))
    comments = post.comments  # This will automatically load the comments
    return render_template('blog/show.html', post=post, comments=comments)

@blog_bp.route('/blog/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a blog post (author and admins only)"""
    post = BlogPost.query.get_or_404(id)

    # Permissions check
    if not (current_user.is_admin or current_user == post.author):
        flash('You do not have permission to edit this post.', 'error')
        return redirect(url_for('blog.show', id=id))

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.author_name = request.form.get('author_name')

        # You could clean/sanitize again here if needed
        # post.title = clean_html_content(post.title)

        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('blog.show', id=post.id))

    return render_template(
        'blog/edit.html',
        post=post,
        cancel_url=url_for('blog.show', id=post.id),
        submit_label="Update Post"
    )



@blog_bp.route('/blog/preview/<int:id>')
@login_required
def preview(id):
    post = BlogPost.query.get_or_404(id)

    # Only allow the author or admins to preview
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this post.', 'error')
        return redirect(url_for('blog.index'))

    return render_template('blog/preview.html', post=post)

@blog_bp.route('/blog/my-posts')
@login_required
@blogger_required
def my_posts():
    posts = BlogPost.query.filter_by(author_id=current_user.id).order_by(BlogPost.created_at.desc()).all()
    return render_template('blog/my_posts.html', posts=posts)

@blog_bp.route('/blog/<int:id>/resubmit', methods=['POST'])
@login_required
@blogger_required
def resubmit(id):
    post = BlogPost.query.get_or_404(id)

    if post.author_id != current_user.id:
        flash('You do not have permission to resubmit this post.', 'error')
        return redirect(url_for('blog.my_posts'))

    if post.status != 'rejected':
        flash('Only rejected posts can be resubmitted.', 'error')
        return redirect(url_for('blog.my_posts'))

    post.status = 'pending_review'
    post.review_notes = None
    db.session.commit()

    flash('Your post has been resubmitted for review.', 'success')
    return redirect(url_for('blog.my_posts'))

@blog_bp.route("/post/create", methods=["POST"])
@login_required
def create_post():
    # ... existing validation code ...

    try:
        new_post = BlogPost(
            title=title,
            content=content,
            author_id=current_user.id,
            status='pending'  # Set initial status as pending
        )
        db.session.add(new_post)
        db.session.commit()

        flash('Your blog post has been submitted for review!', 'success')
        return redirect(url_for('blog.my_posts'))

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating your post. Please try again.', 'error')
        return redirect(url_for('blog.create'))

@blog_bp.route('/blog/<int:post_id>/comments', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a comment to a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('blog.show', id=post_id))
    
    try:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your comment.', 'error')
    
    return redirect(url_for('blog.show', id=post_id))

@blog_bp.route('/blog/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
