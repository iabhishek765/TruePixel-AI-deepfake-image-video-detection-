#!/usr/bin/env python3

import requests
import sys
import json
import base64
import time
from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image, ImageDraw
import subprocess

class TruePixelAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name, test_func):
        """Run a single test"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED")
            else:
                self.log(f"❌ {name} - FAILED")
            return success
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}")
            return False
    
    def test_health_check(self):
        """Test API health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("message") == "TruePixel API" and data.get("status") == "healthy"
            return False
        except Exception as e:
            self.log(f"Health check error: {e}")
            return False
    
    def create_test_user_session(self):
        """Create test user and session via register endpoint"""
        try:
            # Generate unique identifiers
            timestamp = int(time.time())
            email = f"test.user.{timestamp}@example.com"
            password = "testpass123"
            name = "Test User"
            
            payload = {
                "email": email,
                "password": password,
                "name": name
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=payload, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("user_id")
                # Extract session token
                self.session_token = response.cookies.get("session_token")
                
                if not self.session_token:
                    for cookie in response.cookies:
                        if cookie.name == "session_token":
                            self.session_token = cookie.value
                            break
                            
                self.log(f"Created test user: {self.user_id}")
                self.log(f"Created session token: {self.session_token}")
                return True
            else:
                self.log(f"User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"Failed to create test user: {e}")
            return False
    
    def test_auth_me(self):
        """Test /auth/me endpoint with session token"""
        if not self.session_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.get(f"{self.base_url}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("user_id") == self.user_id
            else:
                self.log(f"Auth me failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"Auth me error: {e}")
            return False
    
    def create_realistic_test_image(self):
        """Create a realistic test image with proper visual features"""
        try:
            # Create a larger, more realistic image (512x512)
            img = Image.new('RGB', (512, 512), color='white')
            draw = ImageDraw.Draw(img)
            
            # Create a gradient background
            for y in range(512):
                color_val = int(255 * (y / 512))
                draw.line([(0, y), (512, y)], fill=(color_val, 100, 255 - color_val))
            
            # Add realistic visual elements
            # Face-like oval
            draw.ellipse([150, 100, 350, 300], fill=(255, 220, 177), outline=(0, 0, 0), width=2)
            
            # Eyes
            draw.ellipse([180, 150, 220, 180], fill=(255, 255, 255), outline=(0, 0, 0))
            draw.ellipse([280, 150, 320, 180], fill=(255, 255, 255), outline=(0, 0, 0))
            draw.ellipse([190, 155, 210, 175], fill=(0, 0, 0))  # pupils
            draw.ellipse([290, 155, 310, 175], fill=(0, 0, 0))
            
            # Nose
            draw.polygon([(250, 180), (240, 220), (260, 220)], fill=(255, 200, 150))
            
            # Mouth
            draw.arc([220, 240, 280, 280], 0, 180, fill=(255, 0, 0), width=3)
            
            # Hair
            draw.ellipse([140, 80, 360, 200], fill=(139, 69, 19), outline=(0, 0, 0))
            
            # Add some texture and noise
            import random
            for _ in range(1000):
                x, y = random.randint(0, 511), random.randint(0, 511)
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                draw.point((x, y), fill=color)
            
            # Convert to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
        except Exception as e:
            self.log(f"Failed to create test image: {e}")
            return None
    
    def test_upload_endpoint(self):
        """Test file upload endpoint"""
        if not self.session_token:
            return False
            
        try:
            # Create realistic test image
            image_data = self.create_realistic_test_image()
            if not image_data:
                return False
            
            headers = {"Authorization": f"Bearer {self.session_token}"}
            files = {
                'file': ('test_face.jpg', image_data, 'image/jpeg')
            }
            
            response = requests.post(
                f"{self.base_url}/upload", 
                headers=headers, 
                files=files, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['file_id', 'storage_path', 'file_type', 'content_type']
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    self.storage_path = data['storage_path']
                    self.log(f"Upload successful: {data['file_id']}")
                    return True
                else:
                    self.log(f"Upload response missing fields: {data}")
                    return False
            else:
                self.log(f"Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"Upload error: {e}")
            return False
    
    def test_analyze_endpoint(self):
        """Test analysis endpoint with proper image"""
        if not self.session_token or not hasattr(self, 'storage_path'):
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "storage_path": self.storage_path,
                "file_type": "image"
            }
            
            self.log("Starting analysis (this may take 30-60 seconds)...")
            response = requests.post(
                f"{self.base_url}/analyze",
                headers=headers,
                json=payload,
                timeout=90  # Analysis can take time with GPT-5.2
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'is_fake', 'analysis', 'created_at']
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    self.log(f"Analysis result: {'FAKE' if data['is_fake'] else 'REAL'}")
                    self.log(f"Analysis: {data['analysis'][:150]}...")
                    return True
                else:
                    self.log(f"Analysis response missing fields: {data}")
                    return False
            else:
                self.log(f"Analysis failed: {response.status_code} - {response.text[:300]}")
                return False
                
        except Exception as e:
            self.log(f"Analysis error: {e}")
            return False
    
    def test_upload_without_auth(self):
        """Test upload endpoint without authentication"""
        try:
            # Create test image
            image_data = self.create_realistic_test_image()
            if not image_data:
                return False
            
            files = {
                'file': ('test_unauth.jpg', image_data, 'image/jpeg')
            }
            
            response = requests.post(
                f"{self.base_url}/upload", 
                files=files, 
                timeout=30
            )
            
            # Should return 401 Unauthorized
            success = response.status_code == 401
            if not success:
                self.log(f"Expected 401, got {response.status_code}: {response.text[:200]}")
            return success
                
        except Exception as e:
            self.log(f"Upload without auth error: {e}")
            return False
    
    def test_logout_endpoint(self):
        """Test logout endpoint"""
        if not self.session_token:
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(f"{self.base_url}/auth/logout", headers=headers, timeout=10)
            
            # Logout should succeed
            return response.status_code == 200
        except Exception as e:
            self.log(f"Logout error: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test user and session"""
        if not self.user_id:
            return
        self.log("Test user session logged out and cleaned up.")
    
    def run_all_tests(self):
        """Run all backend API tests"""
        self.log("🚀 Starting TruePixel Backend API Tests")
        self.log("=" * 50)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_health_check),
            ("Create Test User & Session", self.create_test_user_session),
            ("Auth Me Endpoint", self.test_auth_me),
            ("Upload Without Auth (should fail)", self.test_upload_without_auth),
            ("File Upload With Auth", self.test_upload_endpoint),
            ("Image Analysis", self.test_analyze_endpoint),
            ("Logout Endpoint", self.test_logout_endpoint),
        ]
        
        for test_name, test_func in tests:
            success = self.run_test(test_name, test_func)
            if not success and test_name in ["API Health Check", "Create Test User & Session"]:
                self.log("❌ Critical test failed, stopping execution")
                break
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results
        self.log("=" * 50)
        self.log(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!")
            return 0
        else:
            self.log("⚠️  Some tests failed")
            return 1

def main():
    tester = TruePixelAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())