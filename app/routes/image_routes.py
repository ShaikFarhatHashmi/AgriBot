"""
app/routes/image_routes.py — Image Blueprint
=============================================
LAYER  : Routes (URL definitions)
PURPOSE: Maps /image/* URLs to ImageController methods.
"""

from flask import Blueprint, request
from app.controllers.image_controller import ImageController
from app.utils.auth import login_required

image_bp = Blueprint("image", __name__)


@image_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    """Predict plant disease from uploaded image — POST /image/predict."""
    return ImageController.handle_prediction(request.files)


@image_bp.route("/health", methods=["GET"])
def health():
    """Image service health check — GET /image/health."""
    return ImageController.handle_health()