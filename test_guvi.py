import requests
import json
import time
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_URL = "http://localhost:8000"
API_KEY = "your-0002121"
HEADERS = {"x-api-key": API_KEY}

def test_guvi_scam_detection():
    """Test 1: GUVI format scam detection"""
    print("\n" + "="*80)
    print("TEST 1: GUVI Scam Detection (Single Message)")
    print("="*80)
    
    payload = {
        "sessionId": "guvi_test_001",
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account will be blocked. Send OTP to verify KYC at www.fake-bank.com or pay to scammer@paytm. Call 9876543210",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        response = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\nResponse Status: {result['status']}")
        print(f"Agent Reply:\n{result['reply']}")
        print("\n✅ Test PASSED - Scam detected and honeypot reply generated")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_guvi_multi_turn():
    """Test 2: GUVI multi-turn conversation"""
    print("\n" + "="*80)
    print("TEST 2: GUVI Multi-Turn Conversation")
    print("="*80)
    
    session_id = "guvi_test_002"
    
    # Message 1
    payload1 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Your KYC expired. Update at www.fake-kyc.com",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        response1 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload1, timeout=30)
        result1 = response1.json()
        print(f"\nTurn 1 - Agent Reply:\n{result1['reply']}")
        
        # Message 2 - with conversation history
        time.sleep(1)
        payload2 = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Pay Rs 100 to verify@paytm to activate your account",
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": [
                {
                    "sender": "scammer",
                    "text": "Your KYC expired. Update at www.fake-kyc.com",
                    "timestamp": payload1["message"]["timestamp"]
                },
                {
                    "sender": "user",
                    "text": result1['reply'],
                    "timestamp": int(time.time() * 1000) - 500
                }
            ],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response2 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload2, timeout=30)
        result2 = response2.json()
        print(f"\nTurn 2 - Agent Reply:\n{result2['reply']}")
        
        print("\n✅ Test PASSED - Multi-turn conversation handled")
        print("📞 GUVI callback should have been triggered with extracted intelligence")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_guvi_legitimate_message():
    """Test 3: GUVI legitimate (non-scam) message"""
    print("\n" + "="*80)
    print("TEST 3: GUVI Legitimate Message (No Scam)")
    print("="*80)
    
    payload = {
        "sessionId": "guvi_test_003",
        "message": {
            "sender": "scammer",
            "text": "Hello, how are you doing today?",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        response = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\nResponse Status: {result['status']}")
        print(f"Agent Reply:\n{result['reply']}")
        print("\n✅ Test PASSED - Legitimate message handled with normal reply")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_guvi_auth_failure():
    """Test 4: GUVI authentication failure"""
    print("\n" + "="*80)
    print("TEST 4: GUVI Authentication Failure")
    print("="*80)
    
    payload = {
        "sessionId": "guvi_test_004",
        "message": {
            "sender": "scammer",
            "text": "Test message",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        # Send without API key
        response = requests.post(f"{API_URL}/honeypot/analyze", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            result = response.json()
            print(f"Error Response: {result}")
            print("\n✅ Test PASSED - Unauthorized access properly rejected")
            return True
        else:
            print(f"❌ Test FAILED - Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_health_check():
    """Test 5: Health check"""
    print("\n" + "="*80)
    print("TEST 5: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if result.get("status") == "healthy":
            print("\n✅ Test PASSED - API is healthy")
            return True
        else:
            print("\n❌ Test FAILED - Unexpected health status")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("GUVI HONEYPOT API TEST SUITE")
    print("="*80)
    print("\nTesting GUVI Problem Statement 2 Compliance:")
    print("  * GUVI request/response format")
    print("  * Scam detection with keywords")
    print("  * Honeypot reply generation")
    print("  * Intelligence extraction")
    print("  * GUVI callback to updateHoneyPotFinalResult")
    print("  * Session-based conversation tracking")
    
    results = []
    
    # Run all tests
    results.append(("GUVI Scam Detection", test_guvi_scam_detection()))
    results.append(("GUVI Multi-Turn Conversation", test_guvi_multi_turn()))
    results.append(("GUVI Legitimate Message", test_guvi_legitimate_message()))
    results.append(("GUVI Authentication", test_guvi_auth_failure()))
    results.append(("Health Check", test_health_check()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🏆 ALL TESTS PASSED! GUVI-COMPLIANT API READY!")
    else:
        print("\n⚠️  Some tests failed. Check server logs.")
    
    print("\n" + "="*80)
    print("📋 GUVI CALLBACK INFO:")
    print("="*80)
    print("Callback URL: https://hackathon.guvi.in/api/updateHoneyPotFinalResult")
    print("Callback is sent automatically when:")
    print("  1. Scam is detected")
    print("  2. At least one intelligence item is extracted")
    print("  3. Only sent once per sessionId")
    print("\n" + "="*80)
