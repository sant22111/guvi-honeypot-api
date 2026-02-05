import requests
import json

API_URL = "http://localhost:8000/honeypot/analyze"
API_KEY = "your-0002121"

def test_scam_with_grok():
    print("\n=== Testing Scam Detection with Grok API ===")
    headers = {"x-api-key": API_KEY}
    payload = {
        "conversation_id": "test_grok_1",
        "message": "Urgent! Your account has been blocked. Send OTP to verify KYC: www.fake-bank.com",
        "language": "en"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Please start the server first:")
        print("  .\\venv\\Scripts\\uvicorn main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_no_scam():
    print("\n=== Testing Non-Scam Message ===")
    headers = {"x-api-key": API_KEY}
    payload = {
        "conversation_id": "test_grok_2",
        "message": "Hi, how are you doing today?",
        "language": "en"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Honeypot API with Grok (xAI)")
    print("=" * 60)
    
    results = []
    results.append(("No Scam Message", test_no_scam()))
    results.append(("Scam Detection with Grok", test_scam_with_grok()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print("Note: Make sure server is running on port 8000")
    print("Command: .\\venv\\Scripts\\uvicorn main:app --host 0.0.0.0 --port 8000")
    print("=" * 60)
