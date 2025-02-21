from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db
from supabase import create_client, Client
import logging

auth_bp = Blueprint('auth', __name__)

def get_supabase() -> Client:
    return create_client(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_ANON_KEY']
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')
        
        try:
            # Use Supabase auth
            supabase = get_supabase()
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Get or create user in our database
                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(
                        email=email,
                        id=auth_response.user.id
                    )
                    db.session.add(user)
                    db.session.commit()
                
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Login failed. Please check your credentials.', 'error')
            
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash('Invalid email or password', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        
        # Input validation
        if not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            # Register with Supabase
            supabase = get_supabase()
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Create user in our database
                try:
                    user = User(
                        email=email,
                        id=auth_response.user.id
                    )
                    db.session.add(user)
                    db.session.commit()
                    
                    flash('Registration successful! Please check your email to verify your account.', 'success')
                    return redirect(url_for('auth.login'))
                
                except Exception as db_error:
                    logging.error(f"Database error during user creation: {str(db_error)}")
                    # Try to clean up Supabase user if database insert fails
                    try:
                        supabase.auth.admin.delete_user(auth_response.user.id)
                    except:
                        pass
                    flash('An error occurred during registration. Please try again.', 'error')
            else:
                flash('Supabase registration failed. Please try again.', 'error')
                
        except Exception as e:
            logging.error(f"Supabase registration error: {str(e)}")
            error_message = str(e)
            if 'User already registered' in error_message:
                flash('Email already registered. Please login.', 'error')
            else:
                flash(f'Registration failed: {error_message}', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
        logout_user()
        flash('Logged out successfully.', 'success')
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        flash('Error during logout', 'error')
    return redirect(url_for('main.index')) 