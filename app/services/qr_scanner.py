"""
app/services/qr_scanner.py
QR code reading using OpenCV — no external DLL needed on Windows.
OpenCV is already installed in your project via tensorflow dependency.
"""
import cv2
import numpy as np
from PIL import Image


def read_qr_code(image_file):
    """
    Decode QR code from uploaded image using OpenCV.
    Works on Windows without any extra DLL installation.
    """
    try:
        # Open image with PIL and convert to numpy array
        img     = Image.open(image_file).convert("RGB")
        img_arr = np.array(img)

        # Convert RGB → BGR for OpenCV
        img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)

        # Use OpenCV QR code detector
        detector = cv2.QRCodeDetector()
        text, points, _ = detector.detectAndDecode(img_bgr)

        if text and text.strip():
            return {
                "success": True,
                "text":    text.strip(),
                "count":   1,
                "error":   None
            }

        # If first attempt fails try with image enhancement
        # (helps with low contrast or blurry QR codes)
        gray      = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray      = cv2.equalizeHist(gray)             # enhance contrast
        text2, _, _ = detector.detectAndDecode(gray)

        if text2 and text2.strip():
            return {
                "success": True,
                "text":    text2.strip(),
                "count":   1,
                "error":   None
            }

        # Third attempt — resize to help with small QR codes
        h, w   = img_bgr.shape[:2]
        scale  = 2.0 if max(h, w) < 800 else 1.0
        if scale > 1.0:
            enlarged = cv2.resize(img_bgr, (int(w*scale), int(h*scale)),
                                  interpolation=cv2.INTER_CUBIC)
            text3, _, _ = detector.detectAndDecode(enlarged)
            if text3 and text3.strip():
                return {
                    "success": True,
                    "text":    text3.strip(),
                    "count":   1,
                    "error":   None
                }

        return {
            "success": False,
            "text":    None,
            "count":   0,
            "error":   (
                "No QR code found in this image. "
                "Make sure the QR code is clear, well-lit, "
                "and fully visible in the frame."
            )
        }

    except Exception as e:
        return {
            "success": False,
            "text":    None,
            "count":   0,
            "error":   f"Could not read image: {str(e)}"
        }


def build_qr_query(qr_text):
    """
    Convert decoded QR text into a RAG query.
    """
    text  = qr_text.strip()
    query = (
        f"The QR code on this agricultural product says: '{text}'. "
        f"Please explain: what this product is, "
        f"how to use it correctly, recommended dosage, "
        f"which crops it is suitable for, "
        f"any safety precautions, and the approximate market price in India."
    )
    return query





            