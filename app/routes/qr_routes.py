from flask import Blueprint, request
from app.controllers.qr_controller import QRController
from app.utils.auth import login_required

qr_bp = Blueprint("qr", __name__)

@qr_bp.route("/scan", methods=["POST"])
@login_required
def scan():
    """POST /qr/scan — decode QR and explain."""
    return QRController.handle_scan(request.files)