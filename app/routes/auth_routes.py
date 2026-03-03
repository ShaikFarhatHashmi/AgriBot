"""
app/routes/auth_routes.py — Auth Blueprint
==========================================
LAYER  : Routes (URL definitions)
PURPOSE: Maps /auth/* URLs to AuthController methods.
"""

from flask import Blueprint, request
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login():
    """Show login page — GET /auth/login."""
    return AuthController.show_login()


@auth_bp.route("/login", methods=["POST"])
def login_post():
    """Process login form — POST /auth/login."""
    return AuthController.process_login(request.form)


@auth_bp.route("/signup", methods=["GET"])
def signup():
    """Show signup page — GET /auth/signup."""
    return AuthController.show_signup()


@auth_bp.route("/signup", methods=["POST"])
def signup_post():
    """Process signup form — POST /auth/signup."""
    return AuthController.process_signup(request.form)


@auth_bp.route("/logout")
def logout():
    """Logout and redirect — GET /auth/logout."""
    return AuthController.logout()