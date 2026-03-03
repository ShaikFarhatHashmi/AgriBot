import logging
import traceback
from flask import jsonify, current_app
from ..services.qa_service import QAService

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
        query = form_data.get("messageText", "").strip()

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
            logger.info(f"Processing query: {query[:60]}...")
            answer = service.ask(query)
            logger.info(f"Answer: {answer[:80]}...")
            return jsonify({"answer": answer, "status": "success"}), 200

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