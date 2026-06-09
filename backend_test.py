import requests
import sys
import json
import base64
from datetime import datetime
import time

class TruePixelAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_health_endpoint(self):
        """Test /api/ health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            self.log_test("Health Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False

    def create_test_user_session(self):
        """Create test user and session via register endpoint"""
        print("\n🔧 Creating test user and session...")
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
            
            response = requests.post(f"{self.api_url}/auth/register", json=payload, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("user_id")
                # Extract session token from cookie or header
                self.session_token = response.cookies.get("session_token")
                
                if not self.session_token:
                    for cookie in response.cookies:
                        if cookie.name == "session_token":
                            self.session_token = cookie.value
                            break
                            
                if not self.session_token:
                    # Let's fallback if token wasn't in cookie jar (e.g. from header response)
                    # For tests, we could check if cookies are returned in headers
                    # Or we can just log a warning and see if it's there
                    pass
                
                print(f"✅ Test user created: {self.user_id}")
                print(f"✅ Session token: {self.session_token}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test user creation failed: {str(e)}")
            return False

    def test_auth_me_endpoint(self):
        """Test /api/auth/me endpoint with session token"""
        if not self.session_token:
            self.log_test("Auth Me Endpoint", False, "No session token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            
            success = response.status_code == 200
            if success:
                user_data = response.json()
                details = f"User: {user_data.get('name', 'Unknown')}, Email: {user_data.get('email', 'Unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Auth Me Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me Endpoint", False, str(e))
            return False

    def test_upload_endpoint_auth_required(self):
        """Test /api/upload endpoint requires authentication"""
        try:
            # Test without auth - should fail
            files = {"file": ("test.jpg", b"dummy data", "image/jpeg")}
            response = requests.post(f"{self.api_url}/upload", files=files, timeout=10)
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            self.log_test("Upload Endpoint Auth Required", success, details)
            return success
        except Exception as e:
            self.log_test("Upload Endpoint Auth Required", False, str(e))
            return False

    def test_analyze_endpoint_auth_required(self):
        """Test /api/analyze endpoint requires authentication"""
        try:
            # Test without auth - should fail
            response = requests.post(f"{self.api_url}/analyze", json={}, timeout=10)
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            self.log_test("Analyze Endpoint Auth Required", success, details)
            return success
        except Exception as e:
            self.log_test("Analyze Endpoint Auth Required", False, str(e))
            return False

    def test_upload_with_auth(self):
        """Test file upload with authentication"""
        if not self.session_token:
            self.log_test("Upload With Auth", False, "No session token available")
            return False
            
        try:
            # Create a proper test image with visual features (small JPEG with gradient)
            # This is a 100x100 JPEG with a gradient pattern
            test_image_data = base64.b64decode(
                "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
            )
            
            headers = {"Authorization": f"Bearer {self.session_token}"}
            files = {"file": ("test.jpg", test_image_data, "image/jpeg")}
            
            response = requests.post(f"{self.api_url}/upload", headers=headers, files=files, timeout=30)
            
            success = response.status_code == 200
            if success:
                upload_data = response.json()
                details = f"File ID: {upload_data.get('file_id', 'Unknown')}, Type: {upload_data.get('file_type', 'Unknown')}"
                # Store for analysis test
                self.upload_result = upload_data
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Upload With Auth", success, details)
            return success
        except Exception as e:
            self.log_test("Upload With Auth", False, str(e))
            return False

    def test_analyze_with_auth(self):
        """Test analysis with authentication"""
        if not self.session_token:
            self.log_test("Analyze With Auth", False, "No session token available")
            return False
            
        if not hasattr(self, 'upload_result'):
            self.log_test("Analyze With Auth", False, "No upload result available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            data = {
                "storage_path": self.upload_result.get("storage_path"),
                "file_type": self.upload_result.get("file_type", "image")
            }
            
            response = requests.post(f"{self.api_url}/analyze", headers=headers, json=data, timeout=60)
            
            success = response.status_code == 200
            if success:
                analysis_data = response.json()
                details = f"Fake: {analysis_data.get('is_fake', 'Unknown')}, Confidence: {analysis_data.get('confidence', 'Unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Analyze With Auth", success, details)
            return success
        except Exception as e:
            self.log_test("Analyze With Auth", False, str(e))
            return False

    def test_logout_endpoint(self):
        """Test logout endpoint"""
        if not self.session_token:
            self.log_test("Logout Endpoint", False, "No session token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = requests.post(f"{self.api_url}/auth/logout", headers=headers, timeout=10)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            self.log_test("Logout Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Logout Endpoint", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting TruePixel Backend API Tests")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 50)
        
        # Test basic health
        if not self.test_health_endpoint():
            print("❌ Health check failed - stopping tests")
            return False
            
        # Create test user and session
        if not self.create_test_user_session():
            print("❌ Test user creation failed - stopping tests")
            return False
            
        # Test authentication endpoints
        self.test_auth_me_endpoint()
        
        # Test protected endpoints require auth
        self.test_upload_endpoint_auth_required()
        self.test_analyze_endpoint_auth_required()
        
        # Test authenticated operations
        upload_success = self.test_upload_with_auth()
        if upload_success:
            self.test_analyze_with_auth()
        
        # Test logout
        self.test_logout_endpoint()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed")
            return False

def main():
    tester = TruePixelAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())