"""
app/routes/history_routes.py
============================
Routes for chat history API.
All routes require login (via @login_required).
"""
from flask import Blueprint, jsonify, request, session
from app.models.chat_history import (
    get_conversations,
    get_messages,
    get_detections,
    delete_conversation,
    rename_conversation
)
from app.utils.auth import login_required

history_bp = Blueprint("history", __name__)


@history_bp.route("/history/conversations", methods=["GET"])
@login_required
def conversations():
    """
    GET /history/conversations
    Returns all conversations for the logged-in user.
    Used to populate the sidebar on page load.
    """
    user_email = session.get("user_email")
    convs      = get_conversations(user_email)
    return jsonify({"conversations": convs})


@history_bp.route("/history/messages/<conv_id>", methods=["GET"])
@login_required
def messages(conv_id):
    """
    GET /history/messages/<conv_id>
    Returns all chat messages for a conversation.
    Called when user clicks a conversation in the sidebar.
    """
    msgs = get_messages(conv_id)
    return jsonify({"messages": msgs})


@history_bp.route("/history/detections/<conv_id>", methods=["GET"])
@login_required
def detections(conv_id):
    """
    GET /history/detections/<conv_id>
    Returns all disease detection results for a conversation.
    """
    results = get_detections(conv_id)
    return jsonify({"detections": results})


@history_bp.route("/history/delete/<conv_id>", methods=["DELETE"])
@login_required
def delete(conv_id):
    """
    DELETE /history/delete/<conv_id>
    Deletes a conversation and all its messages.
    """
    user_email = session.get("user_email")
    delete_conversation(conv_id, user_email)
    return jsonify({"success": True})


@history_bp.route("/history/rename/<conv_id>", methods=["POST"])
@login_required
def rename(conv_id):
    """
    POST /history/rename/<conv_id>
    Renames a conversation title.
    Body: { "title": "new title" }
    """
    user_email = session.get("user_email")
    new_title  = request.json.get("title", "").strip()
    if not new_title:
        return jsonify({"success": False, "error": "Title cannot be empty"}), 400
    rename_conversation(conv_id, user_email, new_title)
    return jsonify({"success": True})