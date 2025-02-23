from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from supabase import create_client, Client
import logging
from app.extensions import supabase  # We'll add this to extensions.py

auth_bp = Blueprint('auth', __name__)

def get_supabase() -> Client:
    return create_client(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_ANON_KEY']
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Authenticate with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                user = User.query.filter_by(email=email).first()
                if not user:
                    current_app.logger.warning(f"Login attempt for non-existent local user: {email}")
                    flash('Invalid email or password.', 'error')
                    return redirect(url_for('auth.login'))
                
                login_user(user)
                current_app.logger.info(f"User {email} logged in successfully")
                flash('Logged in successfully.', 'success')
                
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)
            
        except Exception as e:
            current_app.logger.error(f"Login error for user {email}: {str(e)}")
            flash('Invalid email or password.', 'error')
    
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
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    try:
        # Get user email before logout for logging
        user_email = current_user.email
        
        # First, log out from Flask-Login
        logout_user()
        
        # Then, log out from Supabase
        try:
            supabase = get_supabase()
            supabase.auth.sign_out()
        except Exception as e:
            current_app.logger.warning(f"Supabase logout failed for user {user_email}: {str(e)}")
            # Continue with the logout process even if Supabase fails
        
        current_app.logger.info(f"User {user_email} logged out successfully")
        flash('You have been logged out.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error during logout: {str(e)}")
        flash('Error during logout. Please try again.', 'error')
    
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            # Send password reset email through Supabase
            result = supabase.auth.reset_password_email(email)
            flash('Password reset link has been sent to your email.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            flash('Error sending reset link. Please try again.', 'error')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # This route handles the actual password reset after clicking email link
    if request.method == 'POST':
        try:
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('auth.reset_password'))
            
            # Get access token from URL (sent by Supabase)
            access_token = request.args.get('access_token')
            
            # Update password in Supabase
            supabase.auth.update_user(
                {"password": new_password},
                access_token
            )
            
            flash('Password has been reset successfully!', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            flash('Error resetting password. Please try again.', 'error')
    
    return render_template('auth/reset_password.html') 