"""
app/controllers/image_controller.py — Image Prediction Controller
"""
import os
import logging
import traceback
from flask import jsonify, current_app, request, session
from app.services.disease_predictor import predict_disease, build_rag_query
from app.services.qa_service import QAService
from app.services.translator import translate_from_english
from app.models.chat_history import create_conversation, save_detection

logger = logging.getLogger(__name__)
_qa_service = None

def _get_service():
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(current_app.config["APP_CONFIG"])
    return _qa_service

class ImageController:

    @staticmethod
    def handle_prediction(files):
        lang       = request.form.get("lang", "en")
        conv_id    = request.form.get("conv_id", "").strip()
        user_email = session.get("user_email")

        if "image" not in files:
            return jsonify({"success": False, "error": "No image uploaded. Send file with field name 'image'."}), 400

        image_file = files["image"]

        if image_file.filename == "":
            return jsonify({"success": False, "error": "No file selected."}), 400

        config    = current_app.config["APP_CONFIG"]
        filename  = image_file.filename.lower()
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension not in config.ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({"success": False, "error": f"Invalid file type '.{extension}'. Allowed types: {config.ALLOWED_IMAGE_EXTENSIONS}"}), 400

        image_file.seek(0, os.SEEK_END)
        file_size_mb = image_file.tell() / (1024 * 1024)
        image_file.seek(0)

        if file_size_mb > config.MAX_IMAGE_SIZE_MB:
            return jsonify({"success": False, "error": f"File too large ({file_size_mb:.1f} MB). Maximum allowed size: {config.MAX_IMAGE_SIZE_MB} MB."}), 400

        try:
            result = predict_disease(image_file)
            logger.info(f"CNN prediction: {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            logger.error(f"CNN prediction failed: {e}\n{traceback.format_exc()}")
            return jsonify({"success": False, "error": "Prediction failed. Please try a different image."}), 500

        rag_query = build_rag_query(result)
        logger.info(f"RAG query: {rag_query}")

        try:
            service    = _get_service()
            rag_answer = service.ask(rag_query)
            logger.info(f"RAG answer received: {rag_answer[:80]}...")
        except Exception as e:
            logger.error(f"RAG service failed: {e}\n{traceback.format_exc()}")
            rag_answer = f"Detected: {result['display_name']}. RAG service unavailable — please consult an agricultural expert."

        # Translate answer to user's language
        final_answer = translate_from_english(rag_answer, lang)
        logger.info(f"Answer translated to lang={lang}")

        # Save detection to history
        if user_email:
            if not conv_id:
                conv_id = create_conversation(user_email, f"Disease scan: {result['display_name']}")
            save_detection(conv_id, result, final_answer, lang)

        response = {
            "success":    True,
            "disease":    result["display_name"],
            "confidence": result["confidence"],
            "reliable":   result["reliable"],
            "rag_answer": final_answer,
            "conv_id":    conv_id,
            "warning":    None
        }

        if not result["reliable"]:
            response["warning"] = (
                f"Low confidence ({result['confidence']}%). "
                f"Result may be inaccurate — try a clearer image with good lighting."
            )
            logger.warning(f"Low confidence prediction: {result['disease']} at {result['confidence']}%")

        return jsonify(response), 200

    @staticmethod
    def handle_health():
        try:
            service = _get_service()
            status  = "ready" if service.is_ready() else "initializing"
            return jsonify({"status": status, "service": "AgriBot Image Prediction", "cnn_model": "loaded", "version": "1.0"}), 200
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 503