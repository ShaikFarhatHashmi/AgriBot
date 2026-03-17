"""
app/routes/qr_routes.py — QR Code Scanner Routes
===============================================
Maps QR-related URLs to QRController methods.
"""

from flask import Blueprint, request, jsonify
from app.controllers.qr_controller import QRController
from app.utils.auth import login_required

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/test-scan", methods=["POST"])
def test_scan():
    """Test QR scan without any authentication - for debugging"""
    try:
        from flask import request
        from app.services.qr_scanner import QRScannerService
        
        if "image" not in request.files:
            return jsonify({
                "success": False,
                "error": "No image uploaded"
            }), 400
        
        image_file = request.files["image"]
        if image_file.filename == "":
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Scan without user context
        scanner = QRScannerService()
        result = scanner.scan_qr_from_image(image_file)
        
        if result['success']:
            return jsonify({
                "success": True,
                "qr_data": result['qr_data'],
                "product_info": result['product_info'],
                "confidence": result['confidence'],
                "format": result['format'],
                "chat_response": f"QR code detected: {result['qr_data']}",
                "conv_id": None
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Scan failed: {str(e)}"
        }), 500


@qr_bp.route("/scan", methods=["POST"])
def scan():
    """Scan QR code image — POST /qr/scan."""
    # Remove authentication requirement completely
    from flask import request
    from app.services.qr_scanner import QRScannerService
    
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "No image uploaded"
        }), 400
    
    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    # Get language from form data
    lang = request.form.get("lang", "en")
    conv_id = request.form.get("conv_id", "").strip()
    
    # Validate image
    scanner = QRScannerService()
    try:
        # Use the scanner's validation method
        is_valid, validation_msg = scanner.validate_image(image_file)
        
        if not is_valid:
            return jsonify({
                "success": False,
                "error": validation_msg
            }), 400
    except:
        # If validation fails, try scanning anyway
        pass
    
    # Scan QR code
    try:
        result = scanner.scan_qr_from_image(image_file)
        
        if result['success']:
            return jsonify({
                "success": True,
                "qr_data": result['qr_data'],
                "product_info": result['product_info'],
                "confidence": result['confidence'],
                "format": result['format'],
                "chat_response": f"QR code detected: {result['qr_data']}",
                "conv_id": conv_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Scan failed: {str(e)}"
        }), 500


@qr_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Upload and scan QR code image — POST /qr/upload."""
    return QRController.handle_upload()


@qr_bp.route("/camera", methods=["POST"])
@login_required
def camera_scan():
    """Scan QR code from camera — POST /qr/camera."""
    return QRController.handle_camera_scan()


@qr_bp.route("/health", methods=["GET"])
def health():
    """QR service health check — GET /qr/health."""
    return QRController.handle_health()
