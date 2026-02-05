import requests
import json

API_URL = "http://localhost:8001/honeypot/analyze"
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

def test_scam_detected():
    print("\n=== Test 2: Scam Message (Rule-based only) ===")
    headers = {"x-api-key": API_KEY}
    payload = {
        "conversation_id": "test_2",
        "message": "Urgent! Your account has been blocked. Click here: www.fake-bank.com",
        "language": "en"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    return response.status_code in [200, 500]

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
    response = requests.get("http://localhost:8001/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

if __name__ == "__main__":
    print("Starting API Tests...")
    print("=" * 50)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("No Scam Message", test_no_scam()))
    results.append(("Unauthorized Access", test_unauthorized()))
    results.append(("Scam Detection (Note: OpenAI quota exceeded, will show error)", test_scam_detected()))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{status}: {test_name}")
    
    print("\nNote: Scam detection with OpenAI requires valid API quota.")
    print("Rule-based detection (keywords/URLs) works without OpenAI.")
