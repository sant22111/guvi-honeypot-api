import requests
import json

API_URL = "http://localhost:8000/honeypot/analyze"
API_KEY = "your-0002121"

def test_no_scam():
    print("\n=== Test 1: No Scam Message ===")
    headers = {"x-api-key": API_KEY}
    payload = {
        "conversation_id": "test_1",
        "message": "Hi, how are you doing today?",
        "language": "en"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_scam_with_gemini():
    print("\n=== Test 2: Scam Message with Gemini ===")
    headers = {"x-api-key": API_KEY}
    payload = {
        "conversation_id": "test_2",
        "message": "Urgent! Your account has been blocked. Send OTP to verify: www.fake-bank.com",
        "language": "en"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_unauthorized():
    print("\n=== Test 3: Unauthorized (Wrong API Key) ===")
    headers = {"x-api-key": "wrong-key"}
    payload = {
        "conversation_id": "test_3",
        "message": "Test message",
        "language": "en"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 401 and response.json().get("error") == "Unauthorized"

def test_health():
    print("\n=== Test 4: Health Check ===")
    response = requests.get("http://localhost:8000/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Honeypot API with Gemini on Port 8000")
    print("=" * 60)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("No Scam Message", test_no_scam()))
    results.append(("Unauthorized Access", test_unauthorized()))
    results.append(("Scam Detection with Gemini", test_scam_with_gemini()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print("Server running on: http://localhost:8000")
    print("Swagger UI: http://localhost:8000/docs")
    print("=" * 60)
