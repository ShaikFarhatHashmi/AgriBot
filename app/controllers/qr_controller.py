"""
app/controllers/qr_controller.py
Handles QR code scanning and RAG explanation.
Same pattern as ImageController.
"""
import logging
import traceback
from flask import jsonify, current_app, request, session
from app.services.qr_scanner import read_qr_code, build_qr_query
from app.services.qa_service import QAService
from app.services.translator import translate_from_english
from app.models.chat_history import create_conversation, save_message

logger      = logging.getLogger(__name__)
_qa_service = None


def _get_service():
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(current_app.config["APP_CONFIG"])
    return _qa_service


class QRController:

    @staticmethod
    def handle_scan(files):
        """
        POST /qr/scan
        Accepts an image of a QR code,
        decodes it, and returns a RAG explanation.
        """
        lang       = request.form.get("lang", "en")
        conv_id    = request.form.get("conv_id", "").strip()
        user_email = session.get("user_email")

        # Validate file
        if "image" not in files:
            return jsonify({
                "success": False,
                "error":   "No image uploaded. Send file with field name 'image'."
            }), 400

        image_file = files["image"]

        if image_file.filename == "":
            return jsonify({
                "success": False,
                "error":   "No file selected."
            }), 400

        # Validate extension
        config    = current_app.config["APP_CONFIG"]
        filename  = image_file.filename.lower()
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension not in config.ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({
                "success": False,
                "error":   f"Invalid file type. Allowed: JPG, PNG, WEBP."
            }), 400

        # Step 1 — Read QR code
        result = read_qr_code(image_file)

        if not result["success"]:
            return jsonify({
                "success": False,
                "error":   result["error"]
            }), 400

        qr_text = result["text"]
        logger.info(f"QR decoded: {qr_text[:80]}")

        # Step 2 — Build RAG query from QR text
        rag_query = build_qr_query(qr_text)

        # Step 3 — Get explanation from RAG pipeline
        try:
            service    = _get_service()
            rag_answer = service.ask(rag_query)
        except Exception as e:
            logger.error(f"RAG failed: {e}\n{traceback.format_exc()}")
            rag_answer = (
                f"QR code read successfully: '{qr_text}'. "
                f"RAG service unavailable — please consult an agricultural expert."
            )

        # Step 4 — Translate to user's language
        final_answer = translate_from_english(rag_answer, lang)

        # Step 5 — Save to chat history
        if user_email:
            if not conv_id:
                conv_id = create_conversation(
                    user_email,
                    f"QR scan: {qr_text[:40]}"
                )
            save_message(conv_id, "user",
                         f"[QR Code scanned]: {qr_text}", lang)
            save_message(conv_id, "bot", final_answer, lang)

        return jsonify({
            "success":    True,
            "qr_text":    qr_text,
            "qr_count":   result["count"],
            "explanation": final_answer,
            "conv_id":    conv_id
        }), 200