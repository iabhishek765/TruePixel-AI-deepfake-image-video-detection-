"""
Test script for TruePixel deepfake detection pipeline.
Tests both real and AI-generated images to verify detection accuracy.
"""
import requests
import sys
import os
import time
import json

API = "http://localhost:8000/api"
SESSION = requests.Session()
AUTH_TOKEN = None

def register_test_user():
    """Register a test user and extract session token."""
    global AUTH_TOKEN
    email = f"test_detect_{int(time.time())}@example.com"
    resp = SESSION.post(f"{API}/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "name": "Detection Tester"
    })
    if resp.status_code == 200:
        # Extract session_token from Set-Cookie header
        cookies = resp.cookies
        token = cookies.get("session_token")
        if token:
            AUTH_TOKEN = token
            print(f"[OK] Registered: {email} (token: {token[:8]}...)")
            return True
        else:
            # Try to find it in headers
            for header_val in resp.headers.get("set-cookie", "").split(";"):
                if "session_token=" in header_val:
                    AUTH_TOKEN = header_val.split("session_token=")[1].strip()
                    print(f"[OK] Registered: {email}")
                    return True
            # Token not found in cookies, try extracting from raw headers
            raw_cookie = resp.headers.get("set-cookie", "")
            if "session_token=" in raw_cookie:
                AUTH_TOKEN = raw_cookie.split("session_token=")[1].split(";")[0].strip()
                print(f"[OK] Registered: {email}")
                return True
            print(f"[WARN] Registered but no session token in cookies")
            print(f"  Response headers: {dict(resp.headers)}")
            return False
    print(f"[FAIL] Auth failed: {resp.status_code} - {resp.text[:200]}")
    return False

def get_auth_headers():
    """Get authorization headers for authenticated requests."""
    if AUTH_TOKEN:
        return {"Authorization": f"Bearer {AUTH_TOKEN}"}
    return {}

def upload_and_analyze(image_path, expected_label):
    """Upload an image and analyze it. Returns (success, result)."""
    filename = os.path.basename(image_path)
    headers = get_auth_headers()
    
    # Upload
    with open(image_path, "rb") as f:
        content_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
        files = {"file": (filename, f, content_type)}
        resp = SESSION.post(f"{API}/upload", files=files, headers=headers)
    
    if resp.status_code != 200:
        print(f"  [FAIL] Upload failed: {resp.status_code} - {resp.text[:200]}")
        return False, None
    
    upload_data = resp.json()
    storage_path = upload_data["storage_path"]
    file_type = upload_data["file_type"]
    print(f"  [UPLOAD] {filename} -> {storage_path}")
    
    # Analyze
    resp = SESSION.post(f"{API}/analyze", json={
        "storage_path": storage_path,
        "file_type": file_type
    }, headers=headers)
    
    if resp.status_code != 200:
        print(f"  [FAIL] Analysis failed: {resp.status_code} - {resp.text[:200]}")
        return False, None
    
    result = resp.json()
    is_fake = result.get("is_fake", None)
    verdict = result.get("verdict", "UNKNOWN")
    analysis = result.get("analysis", "")
    
    # Check if verdict matches expectation
    actual = "FAKE" if is_fake else "REAL"
    correct = actual == expected_label
    status = "[OK]" if correct else "[MISS]"
    
    print(f"  {status} Verdict: {verdict} (expected: {expected_label})")
    print(f"     Analysis:\n{indent(analysis, '       ')}")
    
    # Check no confidence in response
    if "confidence" in result:
        print(f"  [WARN] 'confidence' field still present in response")
    
    return correct, result

def indent(text, prefix):
    """Indent each line of text."""
    return "\n".join(prefix + line for line in text.split("\n"))

def create_test_real_image(path):
    """Create a test image that mimics a real photograph (with sensor noise)."""
    from PIL import Image
    import numpy as np
    
    np.random.seed(42)
    h, w = 256, 256
    
    # Simulate a real photo: natural gradients + significant sensor noise
    x = np.linspace(0, 255, w)
    y = np.linspace(0, 128, h)
    xv, yv = np.meshgrid(x, y)
    
    # Add substantial noise like real camera sensors
    r = (xv * 0.6 + yv * 0.4 + np.random.normal(0, 20, (h, w))).clip(0, 255).astype(np.uint8)
    g = (xv * 0.3 + yv * 0.7 + np.random.normal(0, 22, (h, w))).clip(0, 255).astype(np.uint8)
    b = (xv * 0.5 + yv * 0.2 + np.random.normal(0, 18, (h, w))).clip(0, 255).astype(np.uint8)
    
    img = Image.fromarray(np.stack([r, g, b], axis=2))
    img.save(path)
    print(f"  Created test real image: {path}")

def create_test_fake_image(path):
    """Create a test image that mimics GAN output (smooth, low noise)."""
    from PIL import Image
    import numpy as np
    
    h, w = 256, 256
    
    # GAN-like: ultra-smooth gradients with virtually no noise
    x = np.linspace(50, 200, w)
    y = np.linspace(30, 180, h)
    xv, yv = np.meshgrid(x, y)
    
    r = xv.clip(0, 255).astype(np.uint8)
    g = ((xv + yv) / 2).clip(0, 255).astype(np.uint8)
    b = yv.clip(0, 255).astype(np.uint8)
    
    img = Image.fromarray(np.stack([r, g, b], axis=2))
    img.save(path)
    print(f"  Created test fake image: {path}")

def main():
    print("=" * 60)
    print("TruePixel Deepfake Detection Test Suite")
    print("=" * 60)
    
    # Register test user
    if not register_test_user():
        print("Cannot continue without authentication")
        sys.exit(1)
    
    results = []
    
    # Test 1: AI-generated image (from generate_image tool)
    ai_image_path = r"C:\Users\sarpi\.gemini\antigravity\brain\83d64a39-5560-452a-98a0-1b8e7517d3b9\test_ai_face_1780982415662.png"
    if os.path.exists(ai_image_path):
        print(f"\n--- Test 1: AI-Generated Portrait ---")
        correct, result = upload_and_analyze(ai_image_path, "FAKE")
        results.append(("AI Portrait", correct))
    else:
        print(f"\n--- Test 1: SKIPPED (AI image not found) ---")
    
    # Test 2: Synthetic smooth image (GAN-like)
    fake_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fake.png")
    print(f"\n--- Test 2: Synthetic Smooth Image ---")
    create_test_fake_image(fake_path)
    correct, result = upload_and_analyze(fake_path, "FAKE")
    results.append(("Synthetic Smooth", correct))
    
    # Test 3: Noisy natural image (real-like)
    real_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_real.png")
    print(f"\n--- Test 3: Noisy Natural Image ---")
    create_test_real_image(real_path)
    correct, result = upload_and_analyze(real_path, "REAL")
    results.append(("Noisy Natural", correct))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, c in results if c)
    total = len(results)
    for name, correct in results:
        print(f"  {'[OK]' if correct else '[MISS]':>6} {name}")
    print(f"\nResult: {passed}/{total} passed")
    
    # Cleanup
    for p in [fake_path, real_path]:
        if os.path.exists(p):
            os.remove(p)
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
