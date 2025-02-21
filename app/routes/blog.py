from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import BlogPost, User, BlogCategory
from app import db
from datetime import datetime

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog')
def index():
    """Show all published blog posts"""
    posts = BlogPost.query.filter_by(status='published')\
        .order_by(BlogPost.published_at.desc()).all()
    categories = BlogCategory.query.all()
    return render_template('blog/index.html', posts=posts, categories=categories)

@blog_bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
def new():
    print(f"Current user: {current_user}")
    """Create new blog post (bloggers only)"""
    if not current_user.is_blogger():
        flash('You do not have permission to create blog posts.', 'error')
        return redirect(url_for('blog.index'))
    
    if request.method == 'POST':
        post = BlogPost(
            title=request.form['title'],
            content=request.form['content'],
            author=current_user
        )
        if 'publish' in request.form:
            post.publish()
        
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('blog.show', id=post.id))
    
    return render_template('blog/new.html')

@blog_bp.route('/blog/<int:id>')
def show(id):
    """Show a specific blog post"""
    post = BlogPost.query.get_or_404(id)
    if post.status != 'published' and (not current_user.is_authenticated or post.author != current_user):
        flash('This post is not available.', 'error')
        return redirect(url_for('blog.index'))
    return render_template('blog/show.html', post=post)

@blog_bp.route('/blog/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a blog post (author only)"""
    post = BlogPost.query.get_or_404(id)
    if post.author != current_user:
        flash('You do not have permission to edit this post.', 'error')
        return redirect(url_for('blog.show', id=id))
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        if 'publish' in request.form and post.status != 'published':
            post.publish()
        
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('blog.show', id=post.id))
    
    return render_template('blog/edit.html', post=post)

@blog_bp.route('/blog/category/<slug>')
def category(slug):
    """Show posts in a specific category"""
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    posts = BlogPost.query.filter_by(
        category=category,
        status='published'
    ).order_by(BlogPost.published_at.desc()).all()
    categories = BlogCategory.query.all()
    return render_template('blog/index.html', 
                         posts=posts, 
                         categories=categories, 
                         current_category=category) 