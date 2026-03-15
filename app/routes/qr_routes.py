"""
app/routes/qr_routes.py — QR Code Scanner Routes
===============================================
Maps QR-related URLs to QRController methods.
"""

from flask import Blueprint, request
from app.controllers.qr_controller import QRController
from app.utils.auth import login_required

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/scan", methods=["POST"])
@login_required
def scan():
    """Scan QR code image — POST /qr/scan."""
    return QRController.handle_scan()


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
