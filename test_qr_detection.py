#!/usr/bin/env python3
"""
Test QR detection libraries to identify the issue
"""

import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_opencv():
    """Test OpenCV QR detection"""
    try:
        import cv2
        import numpy as np
        
        logger.info("Testing OpenCV QR detection...")
        
        # Create a simple test QR code image (black square as placeholder)
        test_image = np.zeros((200, 200, 1), dtype=np.uint8)
        # Add a simple pattern that might be detected
        test_image[50:150, 50:150] = 255
        
        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(test_image)
        
        logger.info(f"OpenCV test result: data={data}, points={points is not None}")
        return True
        
    except Exception as e:
        logger.error(f"OpenCV test failed: {e}")
        return False

def test_pyzbar():
    """Test pyzbar QR detection"""
    try:
        from pyzbar import pyzbar
        import cv2
        import numpy as np
        
        logger.info("Testing pyzbar QR detection...")
        
        # Create a simple test image
        test_image = np.zeros((200, 200, 1), dtype=np.uint8)
        test_image[50:150, 50:150] = 255
        
        decoded_objects = pyzbar.decode(test_image)
        logger.info(f"pyzbar test result: found {len(decoded_objects)} objects")
        
        return True
        
    except Exception as e:
        logger.error(f"pyzbar test failed: {e}")
        return False

def test_qrcode_lib():
    """Test qrcode library"""
    try:
        import qrcode
        from PIL import Image
        import io
        
        logger.info("Testing qrcode library...")
        
        # Generate a simple QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("TEST_DATA")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        logger.info("qrcode library test: Successfully generated QR code")
        return True
        
    except Exception as e:
        logger.error(f"qrcode library test failed: {e}")
        return False

def main():
    logger.info("=== QR Detection Library Test ===")
    
    # Test each library
    opencv_ok = test_opencv()
    pyzbar_ok = test_pyzbar()
    qrcode_ok = test_qrcode_lib()
    
    logger.info("\n=== Test Results ===")
    logger.info(f"OpenCV: {'✅ Working' if opencv_ok else '❌ Failed'}")
    logger.info(f"pyzbar: {'✅ Working' if pyzbar_ok else '❌ Failed'}")
    logger.info(f"qrcode: {'✅ Working' if qrcode_ok else '❌ Failed'}")
    
    # Recommendations
    if not pyzbar_ok and not opencv_ok:
        logger.error("\n❌ Both QR detection libraries failed!")
        logger.info("Recommendation: Install pyzbar with proper ZBar library")
        logger.info("On Windows: pip install pyzbar")
        logger.info("On Linux: sudo apt-get install libzbar0 && pip install pyzbar")
    elif pyzbar_ok:
        logger.info("\n✅ pyzbar is working - should be used for QR detection")
    elif opencv_ok:
        logger.info("\n✅ OpenCV is working - will be used as fallback")

if __name__ == "__main__":
    main()
