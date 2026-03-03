"""
app/utils/auth.py — Authentication Utilities
============================================
LAYER  : Utility
PURPOSE: Authentication decorators and session management
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.user import UserModel

def get_current_user():
    """Get current logged-in user from session"""
    if 'user_email' not in session:
        return None
    
    user_model = UserModel()
    return user_model.get_user_by_email(session['user_email'])

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please sign in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        if not user:
            session.clear()
            flash('Your session has expired. Please sign in again.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def logout_user():
    """Logout current user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')

def is_authenticated():
    """Check if user is authenticated"""
    return 'user_email' in session and get_current_user() is not None
