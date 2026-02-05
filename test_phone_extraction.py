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
print("PHONE NUMBER EXTRACTION TEST")
print("="*80)

# Test with explicit phone number
payload = {
    "sessionId": "phone_test_001",
    "message": {
        "sender": "scammer",
        "text": "URGENT! Call 9876543210 or +919876543210 for verification",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}

response = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload, timeout=30)
print(f"Status: {response.status_code}")
print("\nCheck server logs for:")
print("- phoneNumbers should contain: ['9876543210'] or ['9876543210', '+919876543210']")
print("- phoneNumbers should NOT contain empty strings")
print("- bankAccounts should be [] (not contain the 10-digit phone number)")
print("="*80)
