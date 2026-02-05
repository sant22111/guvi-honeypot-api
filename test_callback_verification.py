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

print("\n" + "="*80)
print("GUVI CALLBACK VERIFICATION TEST")
print("="*80)
print("\nThis test will trigger a scam detection with intelligence extraction")
print("and verify the GUVI callback is sent successfully.")
print("\nWatch the server logs for detailed callback information!")
print("="*80)

# Test with a message that has multiple intelligence items
payload = {
    "sessionId": "callback_verify_001",
    "message": {
        "sender": "scammer",
        "text": "URGENT! Your bank account blocked. Pay Rs 500 to verify@paytm or call 9876543210. Visit www.fake-bank-kyc.com",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

print("\nSending scam message with intelligence...")
print(f"Message: {payload['message']['text']}")

try:
    response = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload, timeout=30)
    
    print(f"\n✅ API Response Status: {response.status_code}")
    result = response.json()
    
    print(f"\nAgent Reply:\n{result['reply']}")
    
    print("\n" + "="*80)
    print("NOW CHECK YOUR SERVER LOGS ABOVE FOR:")
    print("="*80)
    print("1. '🔔 SENDING GUVI CALLBACK' message")
    print("2. Payload with extracted intelligence")
    print("3. '✅ GUVI CALLBACK RESPONSE' with status code")
    print("4. Status code should be 200 or 201 for SUCCESS")
    print("\nIf you see '❌ GUVI callback FAILED', investigate the error message")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n")
