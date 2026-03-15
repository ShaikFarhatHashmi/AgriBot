#!/usr/bin/env python3
"""
Simple test script to verify AgriBot app startup
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing AgriBot imports...")

try:
    from app import create_app
    print("✓ App creation import successful")
    
    app = create_app()
    print("✓ App created successfully")
    
    # Test app context
    with app.app_context():
        print("✓ App context working")
        
        # Test disease predictor import
        from app.services.disease_predictor import build_rag_query
        print("✓ Disease predictor import successful")
        
        # Test RAG query builder
        test_result = {"display_name": "Tomato — Late blight"}
        query = build_rag_query(test_result)
        print(f"✓ RAG query working: {query}")
        
    print("\n🎉 All tests passed! AgriBot should work correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
