"""
app/controllers/image_controller.py — Image Prediction Controller
=================================================================
LAYER  : Controller
PURPOSE: Handles plant disease image upload, CNN prediction,
         and RAG-based treatment info retrieval.
"""

import os
import logging
import traceback
from flask import jsonify, current_app
from app.services.disease_predictor import predict_disease, build_rag_query
from app.services.qa_service import QAService

logger = logging.getLogger(__name__)

# ── Lazy service loader — same pattern as chat_controller ─────
_qa_service = None


def _get_service():
    """
    Returns QAService instance.
    Created once on first request, reused after that.
    Matches exact pattern from chat_controller.py.
    """
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(current_app.config["APP_CONFIG"])
    return _qa_service


class ImageController:

    @staticmethod
    def handle_prediction(files):
        """
        POST /image/predict
        Expects : multipart/form-data with field name 'image'
        Returns : JSON with disease name, confidence, treatment info

        Flow:
          1. Validate uploaded file
          2. Run CNN prediction → disease name + confidence
          3. Build RAG query from disease name
          4. Fetch treatment info from ChromaDB via QAService
          5. Return combined response
        """

        # ── STEP 1: Check image field exists ─────────────────
        if "image" not in files:
            return jsonify({
                "success": False,
                "error":   "No image uploaded. Send file with field name 'image'."
            }), 400

        image_file = files["image"]

        # ── STEP 2: Check file is not empty ──────────────────
        if image_file.filename == "":
            return jsonify({
                "success": False,
                "error":   "No file selected."
            }), 400

        # ── STEP 3: Validate file extension ──────────────────
        config    = current_app.config["APP_CONFIG"]
        filename  = image_file.filename.lower()
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension not in config.ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({
                "success": False,
                "error":   (
                    f"Invalid file type '.{extension}'. "
                    f"Allowed types: {config.ALLOWED_IMAGE_EXTENSIONS}"
                )
            }), 400

        # ── STEP 4: Validate file size ────────────────────────
        image_file.seek(0, os.SEEK_END)
        file_size_mb = image_file.tell() / (1024 * 1024)
        image_file.seek(0)                    # reset to start before reading

        if file_size_mb > config.MAX_IMAGE_SIZE_MB:
            return jsonify({
                "success": False,
                "error":   (
                    f"File too large ({file_size_mb:.1f} MB). "
                    f"Maximum allowed size: {config.MAX_IMAGE_SIZE_MB} MB."
                )
            }), 400

        # ── STEP 5: Run CNN prediction ────────────────────────
        try:
            result = predict_disease(image_file)
            logger.info(
                f"CNN prediction: {result['disease']} "
                f"({result['confidence']}% confidence)"
            )
        except Exception as e:
            logger.error(f"CNN prediction failed: {e}\n{traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error":   "Prediction failed. Please try a different image."
            }), 500

        # ── STEP 6: Build RAG query from CNN output ───────────
        # e.g. "What are the symptoms, causes and treatment for Tomato — Late blight?"
        rag_query = build_rag_query(result)
        logger.info(f"RAG query: {rag_query}")

        # ── STEP 7: Fetch treatment info from QAService ───────
        # Uses same service.ask() pattern as ChatController
        try:
            service    = _get_service()
            rag_answer = service.ask(rag_query)
            logger.info(f"RAG answer received: {rag_answer[:80]}...")
        except Exception as e:
            logger.error(f"RAG service failed: {e}\n{traceback.format_exc()}")
            # RAG failure must not hide the CNN result from user
            rag_answer = (
                f"Detected: {result['display_name']}. "
                f"RAG service unavailable — please consult an agricultural expert."
            )

        # ── STEP 8: Build and return final response ───────────
        response = {
            "success":      True,
            "disease":      result["display_name"],  # "Tomato — Late blight"
            "confidence":   result["confidence"],    # 94.26
            "reliable":     result["reliable"],      # True / False
            "rag_answer":   rag_answer,              # treatment info from ChromaDB
            "warning":      None
        }

        # Attach warning if model confidence is below threshold
        if not result["reliable"]:
            response["warning"] = (
                f"Low confidence ({result['confidence']}%). "
                f"Result may be inaccurate — try a clearer image with good lighting."
            )
            logger.warning(
                f"Low confidence prediction: {result['disease']} "
                f"at {result['confidence']}%"
            )

        return jsonify(response), 200

    @staticmethod
    def handle_health():
        """
        GET /image/health
        Checks if CNN model and QAService are both ready.
        Matches same pattern as ChatController.handle_health().
        """
        try:
            service = _get_service()
            status  = "ready" if service.is_ready() else "initializing"
            return jsonify({
                "status":       status,
                "service":      "AgriBot Image Prediction",
                "cnn_model":    "loaded",
                "version":      "1.0"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error":  str(e)
            }), 503