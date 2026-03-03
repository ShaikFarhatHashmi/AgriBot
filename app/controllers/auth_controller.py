"""
app/controllers/auth_controller.py — Authentication Controller
===============================================================
LAYER  : Controller
PURPOSE: Handles login, signup, logout request/response logic.
"""

import logging
from flask import render_template, redirect, url_for, session, flash, request
from app.models.user import UserModel

logger = logging.getLogger(__name__)


class AuthController:
    """Handles all authentication-related routes."""

    @staticmethod
    def show_login():
        """GET /auth/login — render login page."""
        # If user is already logged in, redirect to chat
        if 'user_email' in session:
            return redirect(url_for('chat.index'))
        return render_template("auth/login.html")

    @staticmethod
    def process_login(form_data: dict):
        """
        POST /auth/login — validate credentials and redirect.

        Args:
            form_data: Flask request.form dict

        Returns:
            redirect to chat page on success, back to login on failure
        """
        email    = form_data.get("email", "").strip()
        password = form_data.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for('auth.login'))

        user_model = UserModel()
        result = user_model.authenticate_user(email, password)

        if result["success"]:
            # Store user session
            session['user_email'] = result["user"]["email"]
            session['user_name'] = f"{result['user'].get('first_name', '')} {result['user'].get('last_name', '')}".strip()
            session['first_name'] = result['user'].get('first_name', '')
            session['last_name'] = result['user'].get('last_name', '')
            session['phone'] = result['user'].get('phone', '')
            session['state'] = result['user'].get('state', '')
            
            logger.info(f"User logged in: {email}")
            flash(f"Welcome back, {session['user_name'] or email}!", "success")
            return redirect(url_for('chat.index'))
        else:
            flash(result["error"], "error")
            logger.warning(f"Login failed for: {email}")
            return redirect(url_for('auth.login'))

    @staticmethod
    def show_signup():
        """GET /auth/signup — render signup page."""
        # If user is already logged in, redirect to chat
        if 'user_email' in session:
            return redirect(url_for('chat.index'))
        return render_template("auth/signup.html")

    @staticmethod
    def process_signup(form_data: dict):
        """
        POST /auth/signup — register new user and redirect.

        Args:
            form_data: Flask request.form dict
        """
        first_name = form_data.get("first_name", "").strip()
        last_name  = form_data.get("last_name", "").strip()
        email      = form_data.get("email", "").strip()
        password   = form_data.get("password", "").strip()
        phone      = form_data.get("phone", "").strip()
        state      = form_data.get("state", "").strip()

        if not all([first_name, email, password]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('auth.signup'))

        user_model = UserModel()
        result = user_model.create_user(email, password, first_name, last_name, phone, state)

        if result["success"]:
            # Auto-login after successful signup
            session['user_email'] = result["user"]["email"]
            session['user_name'] = f"{result['user'].get('first_name', '')} {result['user'].get('last_name', '')}".strip()
            session['first_name'] = result['user'].get('first_name', '')
            session['last_name'] = result['user'].get('last_name', '')
            session['phone'] = result['user'].get('phone', '')
            session['state'] = result['user'].get('state', '')
            
            logger.info(f"New user registered: {email}")
            flash(f"Welcome to AgriBot, {first_name}! Your account has been created.", "success")
            return redirect(url_for('chat.index'))
        else:
            flash(result["error"], "error")
            logger.warning(f"Signup failed for: {email}")
            return redirect(url_for('auth.signup'))

    @staticmethod
    def logout():
        """GET /auth/logout — clear session and redirect to login."""
        user_email = session.get('user_email', 'Unknown')
        session.clear()
        logger.info(f"User logged out: {user_email}")
        flash("You have been logged out successfully.", "success")
        return redirect(url_for('auth.login'))