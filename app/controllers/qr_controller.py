"""
app/controllers/qr_controller.py — QR Code Scanning Controller
================================================================
Handles QR code upload, scanning, and integration with chat system.
"""

import os
import logging
import traceback
import json
from flask import jsonify, current_app, request, session
from app.services.qr_scanner import QRScannerService
from app.services.qa_service import QAService
from app.services.translator import translate_from_english
from app.models.chat_history import create_conversation, save_qr_scan

logger = logging.getLogger(__name__)
_qr_service = None
_qa_service = None


def _get_qr_service():
    global _qr_service
    if _qr_service is None:
        _qr_service = QRScannerService(current_app.config["APP_CONFIG"])
    return _qr_service


def _get_qa_service():
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService(current_app.config["APP_CONFIG"])
    return _qa_service


class QRController:

    @staticmethod
    def handle_upload():
        """Handle QR code image upload and scanning."""
        lang = request.form.get("lang", "en")
        conv_id = request.form.get("conv_id", "").strip()
        user_email = session.get("user_email")

        if "image" not in request.files:
            return jsonify({
                "success": False,
                "error": "No image uploaded. Send file with field name 'image'."
            }), 400

        image_file = request.files["image"]

        if image_file.filename == "":
            return jsonify({
                "success": False,
                "error": "No file selected."
            }), 400

        # Validate image
        qr_service = _get_qr_service()
        is_valid, validation_msg = qr_service.validate_image(image_file)
        
        if not is_valid:
            return jsonify({
                "success": False,
                "error": validation_msg
            }), 400

        try:
            # Scan QR code
            scan_result = qr_service.scan_qr_from_image(image_file)
            
            if not scan_result["success"]:
                return jsonify({
                    "success": False,
                    "error": scan_result["error"]
                }), 400

            logger.info(f"QR code scanned: {scan_result['qr_data'][:50]}...")

            # Generate chat response about the QR content
            chat_response = QRController._generate_qr_response(scan_result, lang)
            
            # Save to chat history
            if user_email:
                if not conv_id:
                    conv_id = create_conversation(
                        user_email, 
                        f"QR Scan: {scan_result['qr_data'][:30]}..."
                    )
                
                save_qr_scan(
                    conv_id, 
                    scan_result, 
                    chat_response, 
                    lang
                )

            return jsonify({
                "success": True,
                "qr_data": scan_result["qr_data"],
                "product_info": scan_result["product_info"],
                "confidence": scan_result["confidence"],
                "format": scan_result["format"],
                "chat_response": chat_response,
                "conv_id": conv_id
            }), 200

        except Exception as e:
            logger.error(f"QR scanning failed: {e}\n{traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error": "QR scanning failed. Please try again."
            }), 500

    @staticmethod
    def handle_scan():
        """Handle QR code scanning from uploaded image file."""
        try:
            # Get form data
            lang = request.form.get("lang", "en")
            conv_id = request.form.get("conv_id", "").strip()
            user_email = session.get("user_email")

            # Check if image file is provided
            if "image" not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No image uploaded. Send file with field name 'image'."
                }), 400

            image_file = request.files["image"]

            if image_file.filename == "":
                return jsonify({
                    "success": False,
                    "error": "No file selected."
                }), 400

            # Validate image
            qr_service = _get_qr_service()
            is_valid, validation_msg = qr_service.validate_image(image_file)
            
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": validation_msg
                }), 400

            # Scan QR code
            scan_result = qr_service.scan_qr_from_image(image_file)
            
            if not scan_result["success"]:
                return jsonify({
                    "success": False,
                    "error": scan_result["error"]
                }), 400

            logger.info(f"QR code scanned: {scan_result['qr_data'][:50]}...")

            # Generate chat response about the QR content
            chat_response = QRController._generate_qr_response(scan_result, lang)
            
            # Save to chat history
            if user_email:
                if not conv_id:
                    conv_id = create_conversation(
                        user_email, 
                        f"QR Scan: {scan_result['qr_data'][:30]}..."
                    )
                
                save_qr_scan(
                    conv_id, 
                    scan_result, 
                    chat_response, 
                    lang
                )

            return jsonify({
                "success": True,
                "qr_data": scan_result["qr_data"],
                "product_info": scan_result["product_info"],
                "confidence": scan_result["confidence"],
                "format": scan_result["format"],
                "chat_response": chat_response,
                "conv_id": conv_id,
                "universal_query": scan_result.get("universal_query", ""),
                "agricultural_context": scan_result.get("agricultural_context"),
                "is_agricultural": scan_result.get("is_agricultural", False)
            }), 200

        except Exception as e:
            logger.error(f"QR scanning failed: {e}\n{traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error": "QR scanning failed. Please try again."
            }), 500

    @staticmethod
    def handle_camera_scan():
        """Handle QR code scanning from camera data (base64 image)."""
        try:
            data = request.get_json()
            
            if not data or "image_data" not in data:
                return jsonify({
                    "success": False,
                    "error": "No image data provided"
                }), 400

            import base64
            from io import BytesIO
            
            # Decode base64 image
            image_data = data["image_data"]
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image_file = BytesIO(image_bytes)
            
            lang = data.get("lang", "en")
            conv_id = data.get("conv_id", "").strip()
            user_email = session.get("user_email")

            # Scan QR code
            qr_service = _get_qr_service()
            scan_result = qr_service.scan_qr_from_image(image_file)
            
            if not scan_result["success"]:
                return jsonify({
                    "success": False,
                    "error": scan_result["error"]
                }), 400

            logger.info(f"QR code scanned from camera: {scan_result['qr_data'][:50]}...")

            # Generate chat response
            chat_response = QRController._generate_qr_response(scan_result, lang)
            
            # Save to chat history
            if user_email:
                if not conv_id:
                    conv_id = create_conversation(
                        user_email, 
                        f"QR Scan: {scan_result['qr_data'][:30]}..."
                    )
                
                save_qr_scan(
                    conv_id, 
                    scan_result, 
                    chat_response, 
                    lang
                )

            return jsonify({
                "success": True,
                "qr_data": scan_result["qr_data"],
                "product_info": scan_result["product_info"],
                "confidence": scan_result["confidence"],
                "format": scan_result["format"],
                "chat_response": chat_response,
                "conv_id": conv_id
            }), 200

        except Exception as e:
            logger.error(f"Camera QR scanning failed: {e}\n{traceback.format_exc()}")
            return jsonify({
                "success": False,
                "error": "Camera QR scanning failed. Please try again."
            }), 500

    @staticmethod
    def _generate_qr_response(scan_result, lang="en"):
        """Generate chat response about QR code content."""
        try:
            qa_service = _get_qa_service()
            
            # Build query based on QR content
            qr_data = scan_result["qr_data"]
            product_info = scan_result["product_info"]
            
            if product_info and product_info.get("type") == "url":
                query = f"I scanned a QR code that contains this URL: {qr_data}. Can you tell me about this product or website?"
            elif product_info and product_info.get("type") == "product_id":
                query = f"I scanned a QR code with product ID: {qr_data}. What information can you provide about this product?"
            elif product_info and product_info.get("type") == "structured":
                query = f"I scanned a QR code with this information: {qr_data}. Can you explain what this product is and provide details?"
            else:
                query = f"I scanned a QR code containing: {qr_data}. Can you help me understand what this is about?"
            
            # Get AI response
            ai_response = qa_service.ask(query)
            
            # Translate if needed
            if lang != "en":
                final_response = translate_from_english(ai_response, lang)
            else:
                final_response = ai_response
            
            return final_response

        except Exception as e:
            logger.error(f"Failed to generate QR response: {e}")
            
            # Fallback response
            if lang == "en":
                return f"I found a QR code with data: {scan_result['qr_data']}. This appears to be {scan_result['product_info'].get('type', 'general content')}. For more detailed information, you may need to check the product directly or contact the manufacturer."
            else:
                return translate_from_english(
                    f"I found a QR code with data: {scan_result['qr_data']}. This appears to be {scan_result['product_info'].get('type', 'general content')}. For more detailed information, you may need to check the product directly or contact the manufacturer.",
                    lang
                )

    @staticmethod
    def handle_health():
        """QR service health check."""
        try:
            qr_service = _get_qr_service()
            qa_service = _get_qa_service()
            
            return jsonify({
                "status": "ready",
                "service": "AgriBot QR Scanner",
                "features": ["upload_scan", "camera_scan", "chat_integration"],
                "version": "1.0"
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), 503
