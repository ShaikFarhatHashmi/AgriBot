#!/usr/bin/env python3
"""
Create a test QR code image for testing the QR scanner
"""

import qrcode
from PIL import Image
import io

def create_test_qr():
    """Create a simple test QR code"""
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data("https://www.example.com/test-qr-code-12345")
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save as PNG
    img.save("test_qr_code.png")
    print("✅ Test QR code saved as 'test_qr_code.png'")
    
    # Also save a high-quality version
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((300, 300), Image.Resampling.LANCZOS)
    img.save("test_qr_code_hq.png")
    print("✅ High-quality test QR code saved as 'test_qr_code_hq.png'")
    
    # Print the QR data for verification
    qr_data = "https://www.example.com/test-qr-code-12345"
    print(f"📱 QR code contains: {qr_data}")
    
    return qr_data

if __name__ == "__main__":
    print("🔧 Creating test QR codes...")
    data = create_test_qr()
    print(f"🎯 Use these images to test the QR scanner!")
    print(f"📱 Expected result: {data}")
