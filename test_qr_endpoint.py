#!/usr/bin/env python3
"""
Test the QR endpoint exactly like the frontend calls it
"""

import requests
import base64
import io
from PIL import Image

def test_qr_endpoint():
    """Test the /qr/scan endpoint with a test QR code"""
    
    # Load the test QR code
    with open('test_qr_code.png', 'rb') as f:
        image_data = f.read()
    
    # Create form data like the frontend does
    files = {'image': ('test_qr_code.png', image_data, 'image/png')}
    data = {
        'lang': 'en',
        'conv_id': ''
    }
    
    print("🔧 Testing /qr/scan endpoint...")
    print(f"📱 Image size: {len(image_data)} bytes")
    print(f"📱 Language: {data['lang']}")
    
    try:
        # Make the request exactly like the frontend
        response = requests.post(
            'http://127.0.0.1:5000/qr/scan',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📊 Response JSON: {response_json}")
            
            if response_json.get('success'):
                print(f"✅ QR scan successful: {response_json.get('qr_data')}")
            else:
                print(f"❌ QR scan failed: {response_json.get('error')}")
                
        except Exception as e:
            print(f"📊 Response text: {response.text}")
            print(f"❌ Failed to parse JSON: {e}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure AgriBot is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_qr_endpoint()
