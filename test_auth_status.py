#!/usr/bin/env python3
"""
Test authentication status and QR scanner with proper session
"""

import requests
import base64

def test_auth_and_qr():
    """Test authentication and QR scanner with session management"""
    
    session = requests.Session()
    
    print("🔧 Testing authentication and QR scanner...")
    
    # First, check if we can access the main page
    print("\n1. Testing main page access...")
    response = session.get('http://127.0.0.1:5000/')
    print(f"   Status: {response.status_code}")
    
    if 'login' in response.text.lower():
        print("   ❌ Not logged in - need to authenticate")
        
        # Try to login with a test account (if available)
        print("\n2. Attempting login...")
        login_data = {
            'email': 'test@example.com',  # Replace with actual email
            'password': 'password'        # Replace with actual password
        }
        
        login_response = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if 'login' in login_response.text.lower():
            print("   ❌ Login failed - please check credentials")
            print("   📝 Please manually log in to AgriBot first")
            return
        else:
            print("   ✅ Login successful")
    else:
        print("   ✅ Already logged in")
    
    # Now test the QR scanner with the authenticated session
    print("\n3. Testing QR scanner with authenticated session...")
    
    # Load the test QR code
    with open('test_qr_code.png', 'rb') as f:
        image_data = f.read()
    
    files = {'image': ('test_qr_code.png', image_data, 'image/png')}
    data = {
        'lang': 'en',
        'conv_id': ''
    }
    
    try:
        response = session.post(
            'http://127.0.0.1:5000/qr/scan',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"   QR scan status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                print(f"   Response: {response_json}")
                
                if response_json.get('success'):
                    print(f"   ✅ QR scan successful: {response_json.get('qr_data')}")
                else:
                    print(f"   ❌ QR scan failed: {response_json.get('error')}")
            except Exception as e:
                print(f"   ❌ Failed to parse JSON: {e}")
                print(f"   Response text: {response.text[:200]}...")
        else:
            print(f"   ❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    test_auth_and_qr()
