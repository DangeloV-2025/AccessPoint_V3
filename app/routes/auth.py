from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from supabase import create_client, Client
import logging
from app.extensions import supabase  # We'll add this to extensions.py
from datetime import datetime, timedelta
import secrets

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
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # First check if user already exists in our database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email is already registered. Please login instead.', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            current_app.logger.info(f"Attempting to register user: {email}")
            
            # Create user in Supabase
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            current_app.logger.info(f"Supabase registration response: {auth_response}")
            
            if auth_response.user:
                # Create local user
                user = User(
                    id=auth_response.user.id,
                    email=email
                )
                
                try:
                    db.session.add(user)
                    db.session.commit()
                    
                    current_app.logger.info(f"Successfully created local user record for {email}")
                    flash('Registration successful! You can now login.', 'success')
                    login_user(user)
                    return redirect(url_for('main.index'))
                except Exception as db_error:
                    db.session.rollback()
                    current_app.logger.error(f"Database error during user creation: {str(db_error)}")
                    
                    # Check if this is a duplicate user error
                    if "unique constraint" in str(db_error).lower() and "email" in str(db_error).lower():
                        # User already exists in our database, try to log them in
                        existing_user = User.query.filter_by(email=email).first()
                        if existing_user:
                            login_user(existing_user)
                            flash('You are now logged in.', 'success')
                            return redirect(url_for('main.index'))
                    
                    flash('An error occurred during registration. Please try again.', 'error')
                    return redirect(url_for('auth.register'))
            else:
                current_app.logger.error(f"Failed to create Supabase user for {email}")
                flash('Registration failed. Please try again.', 'error')
        except Exception as e:
            current_app.logger.error(f"Registration error for {email}: {str(e)}")
            # Check if the error is because the user already exists in Supabase
            if "User already registered" in str(e):
                # Try to find the user in our database
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    # User exists in both Supabase and our database, log them in
                    login_user(existing_user)
                    flash('You are now logged in.', 'success')
                    return redirect(url_for('main.index'))
                else:
                    # User exists in Supabase but not in our database
                    # Try to get the user ID from Supabase
                    try:
                        # Try to sign in to get the user ID
                        auth_response = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        
                        if auth_response.user:
                            # Create the user in our database
                            user = User(
                                id=auth_response.user.id,
                                email=email
                            )
                            db.session.add(user)
                            db.session.commit()
                            
                            login_user(user)
                            flash('You are now logged in.', 'success')
                            return redirect(url_for('main.index'))
                    except Exception as login_error:
                        current_app.logger.error(f"Error during login after registration: {str(login_error)}")
                        
                flash('This email is already registered. Please login instead.', 'error')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.', 'error')
    
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
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        try:
            # Send password reset email via Supabase - they will generate the token
            supabase.auth.reset_password_for_email(
                email,
                {
                    "redirect_to": url_for('auth.verify_reset', _external=True)
                }
            )
            
            # Only store email in session
            session['reset_email'] = email
            
            current_app.logger.info(f"Password reset requested for {email}")
            flash('Check your email for the password reset code.', 'success')
            return redirect(url_for('auth.verify_reset'))
            
        except Exception as e:
            current_app.logger.error(f"Password reset error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify-reset', methods=['GET', 'POST'])
def verify_reset():
    """Verify token and allow password reset"""
    if request.method == 'POST':
        token = request.form.get('otp')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        email = session.get('reset_email')  # Get email from session
        
        current_app.logger.info(f"Received Supabase token for verification: {token}")
        
        if not all([token, new_password, confirm_password, email]):
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.verify_reset'))
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.verify_reset'))
        
        try:
            # Verify the OTP with both email and token
            response = supabase.auth.verify_otp({
                "email": email,
                "token": token,
                "type": "recovery"
            })
            
            current_app.logger.info("Supabase token verified successfully")
            
            # Update the password
            supabase.auth.update_user({
                "password": new_password
            })
            
            # Clear session
            session.pop('reset_email', None)
            
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f"Password reset verification error: {str(e)}")
            flash('Invalid or expired reset code. Please try again.', 'error')
    
    return render_template('auth/verify_reset.html') 