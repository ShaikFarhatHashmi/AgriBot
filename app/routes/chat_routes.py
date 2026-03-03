"""
app/routes/chat_routes.py — Chat Blueprint
==========================================
LAYER  : Routes (URL definitions)
PURPOSE: Maps URLs to ChatController methods.

Routes are thin — no logic here, just URL → controller mapping.
"""

from flask import Blueprint, request, render_template, session
from app.controllers.chat_controller import ChatController
from app.utils.auth import login_required, get_current_user

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
@login_required
def index():
    """Render main chatbot page."""
    user = get_current_user()
    return render_template("chat/index.html", user=user)


@chat_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    """Handle chat query — POST /ask."""
    return ChatController.handle_query(request.form)


@chat_bp.route("/health", methods=["GET"])
def health():
    """Service health check — GET /health."""
    return ChatController.handle_health()