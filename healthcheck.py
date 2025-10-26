#!/usr/bin/env python3
"""
Health check script for Cloud Run deployment
"""
import requests
import sys
import os

def health_check():
    """Perform a simple health check"""
    try:
        port = os.environ.get("PORT", "8080")
        url = f"http://localhost:{port}/health"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)