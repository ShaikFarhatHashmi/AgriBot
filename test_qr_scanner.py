#!/usr/bin/env python3
"""
Test script to verify QR scanner functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.qr_scanner import QRScannerService
from settings import AppConfig

def test_qr_scanner():
    """Test the QR scanner service"""
    print("🧪 Testing QR Scanner Service...")
    
    # Initialize service
    config = AppConfig()
    scanner = QRScannerService(config)
    
    # Test 1: Text QR data
    print("\n📱 Test 1: Text QR Data")
    text_result = scanner.scan_qr_data("https://www.amazon.com/dp/B08N5WRWNW", is_image_data=False)
    print(f"Status: {text_result['status']}")
    print(f"Type: {text_result['type']}")
    print(f"Confidence: {text_result['confidence']:.1%}")
    print(f"Universal Query: {text_result.get('universal_query', 'N/A')[:100]}...")
    
    # Test 2: Agricultural content
    print("\n🌾 Test 2: Agricultural Content")
    agri_result = scanner.scan_qr_data("fertilizer urea dap npk compost", is_image_data=False)
    print(f"Status: {agri_result['status']}")
    print(f"Type: {agri_result['type']}")
    print(f"Is Agricultural: {agri_result.get('is_agricultural', False)}")
    print(f"Agricultural Context: {agri_result.get('agricultural_context', 'N/A')}")
    print(f"Universal Query: {agri_result.get('universal_query', 'N/A')[:100]}...")
    
    # Test 3: WiFi QR data
    print("\n📶 Test 3: WiFi QR Data")
    wifi_result = scanner.scan_qr_data("WIFI:T:WPA;S:HomeNetwork_5G;P:MySecurePassword123;H:false;", is_image_data=False)
    print(f"Status: {wifi_result['status']}")
    print(f"Type: {wifi_result['type']}")
    print(f"Extracted Info: {wifi_result['extracted_info']}")
    print(f"Universal Query: {wifi_result.get('universal_query', 'N/A')[:100]}...")
    
    print("\n✅ QR Scanner Service Tests Complete!")
    return True

if __name__ == "__main__":
    try:
        test_qr_scanner()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
