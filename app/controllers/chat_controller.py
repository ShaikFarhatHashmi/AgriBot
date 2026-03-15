import logging
import traceback
from flask import jsonify, current_app, session
from ..services.qa_service import QAService
from app.services.translator import translate_to_english, translate_from_english
from app.models.chat_history import create_conversation, save_message

logger = logging.getLogger(__name__)
_qa_service = None


def _get_service():
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(current_app.config["APP_CONFIG"])
    return _qa_service


class ChatController:

    @staticmethod
    def handle_query(form_data):
        query      = form_data.get("messageText", "").strip()
        lang       = form_data.get("lang", "en")
        conv_id    = form_data.get("conv_id", "").strip()   # current session ID from frontend
        user_email = session.get("user_email")              # from your auth system

        if not query:
            return jsonify({"error": "Empty query", "answer": "Please enter a question."}), 400

        if len(query) > 500:
            return jsonify({"error": "Too long", "answer": "Keep question under 500 characters."}), 400

        try:
            service = _get_service()
        except Exception as e:
            logger.error(f"Service init failed: {e}\n{traceback.format_exc()}")
            return jsonify({"error": "Service unavailable", "answer": "Chatbot failed to start. Check your setup."}), 503

        try:
            logger.info(f"Processing query: {query[:60]}... [lang={lang}]")

            # ── STEP 1: Translate input → English ─────────────
            english_query = translate_to_english(query, lang)

            # ── STEP 2: RAG pipeline (unchanged) ──────────────
            answer = service.ask(english_query)

            # ── STEP 3: Translate answer → user's language ────
            final_answer = translate_from_english(answer, lang)

            # ── STEP 4: Save to chat history ──────────────────
            if user_email:
                # First message of a new session → create conversation
                if not conv_id:
                    conv_id = create_conversation(user_email, query)

                save_message(conv_id, "user", query, lang)
                save_message(conv_id, "bot",  final_answer, lang)

            logger.info(f"Answer ready. conv_id={conv_id}")

            return jsonify({
                "answer":  final_answer,
                "conv_id": conv_id,     # send back so JS tracks the active session
                "status":  "success"
            }), 200

        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return jsonify({"error": "Connection error", "answer": "Cannot reach AI service."}), 503

        except Exception as e:
            logger.error(f"Query error: {e}\n{traceback.format_exc()}")
            return jsonify({"error": "Processing error", "answer": "Something went wrong. Try again."}), 500

    @staticmethod
    def handle_health():
        try:
            service = _get_service()
            status  = "ready" if service.is_ready() else "initializing"
            return jsonify({"status": status, "service": "AgriBot", "version": "2.0"}), 200
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 503