from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.has_role(role_name):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def blogger_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_blogger() or current_user.is_admin):
            flash('You do not have permission to create blog posts.', 'error')
            return redirect(url_for('blog.index'))
        return f(*args, **kwargs)
    return decorated_function 