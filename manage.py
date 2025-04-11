#!/usr/bin/env python3
import sys
import os

# Make sure your environment variables are loaded
# e.g. by using python-dotenv or pre-exporting environment
# variables before running this script.

from app import create_app, db
from app.models.user import User, Role

def add_role_to_user(email, role_name):
    """
    Check if user with 'email' exists.
    If yes, assign them the specified role.
    """
    # Create a Flask app context
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found.")
            return

        # Get or create the specified role
        role, _ = Role.get_or_create(name=role_name)

        # Check if the user already has the role
        if user.has_role(role_name):
            print(f"User '{email}' already has the role '{role_name}'.")
            return

        # Assign the role
        user.roles.append(role)
        db.session.commit()
        print(f"Role '{role_name}' added to user '{email}' successfully.")

if __name__ == '__main__':
    """
    Usage:
        python manage.py <email> <role_name>

    Example:
        python manage.py testuser@example.com admin
    """
    if len(sys.argv) != 3:
        print("Usage: python manage.py <email> <role_name>")
        sys.exit(1)

    email_arg = sys.argv[1]
    role_arg = sys.argv[2]

    add_role_to_user(email_arg, role_arg)
