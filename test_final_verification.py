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
print("FINAL VERIFICATION TEST - Bug Fixes")
print("="*80)

# Test 1: Phone number should NOT appear in bankAccounts
print("\n[TEST 1] Phone number (10 digits) should NOT be in bankAccounts")
payload1 = {
    "sessionId": "final_test_001",
    "message": {
        "sender": "scammer",
        "text": "Call 9876543210 for help",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}

response1 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload1, timeout=30)
print(f"Status: {response1.status_code}")

# Test 2: Real bank account (12-16 digits) should appear in bankAccounts
print("\n[TEST 2] Real bank account (12+ digits) should be in bankAccounts")
payload2 = {
    "sessionId": "final_test_002",
    "message": {
        "sender": "scammer",
        "text": "Transfer to account 123456789012 at HDFC Bank",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}

response2 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload2, timeout=30)
print(f"Status: {response2.status_code}")

# Test 3: Empty strings should NOT appear in phoneNumbers
print("\n[TEST 3] No empty strings in phoneNumbers array")
payload3 = {
    "sessionId": "final_test_003",
    "message": {
        "sender": "scammer",
        "text": "URGENT! Pay to verify@paytm. Visit www.scam.com",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}

response3 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload3, timeout=30)
print(f"Status: {response3.status_code}")

print("\n" + "="*80)
print("CHECK SERVER LOGS FOR GUVI CALLBACK PAYLOADS")
print("="*80)
print("\nVerify:")
print("1. phoneNumbers should be [] or have valid numbers (NO empty strings)")
print("2. bankAccounts should NOT contain 10-digit phone numbers")
print("3. bankAccounts should contain 11+ digit account numbers")
print("="*80)
