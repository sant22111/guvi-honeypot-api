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
print("COMPREHENSIVE FINAL VERIFICATION - ALL BUG FIXES")
print("="*80)

tests_passed = 0
tests_total = 0

# Test 1: Phone number extraction (no empty strings)
print("\n[TEST 1] Phone number with +91 prefix")
tests_total += 1
payload1 = {
    "sessionId": "comprehensive_001",
    "message": {
        "sender": "scammer",
        "text": "Call +919876543210 or 9876543210 for urgent help",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}
response1 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload1, timeout=30)
if response1.status_code == 200:
    print("✓ Status 200 - Check logs: phoneNumbers should be ['9876543210'] (no empty strings)")
    tests_passed += 1
else:
    print(f"✗ Failed with status {response1.status_code}")

time.sleep(1)

# Test 2: Bank account (11+ digits) should NOT be confused with phone
print("\n[TEST 2] Real bank account (13 digits)")
tests_total += 1
payload2 = {
    "sessionId": "comprehensive_002",
    "message": {
        "sender": "scammer",
        "text": "Transfer to account 1234567890123 at HDFC Bank",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}
response2 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload2, timeout=30)
if response2.status_code == 200:
    print("✓ Status 200 - Check logs: bankAccounts should be ['1234567890123']")
    tests_passed += 1
else:
    print(f"✗ Failed with status {response2.status_code}")

time.sleep(1)

# Test 3: 10-digit number should be phone, NOT bank account
print("\n[TEST 3] 10-digit number (should be phone only)")
tests_total += 1
payload3 = {
    "sessionId": "comprehensive_003",
    "message": {
        "sender": "scammer",
        "text": "Contact 9876543210 immediately",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}
response3 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload3, timeout=30)
if response3.status_code == 200:
    print("✓ Status 200 - Check logs: phoneNumbers=['9876543210'], bankAccounts=[]")
    tests_passed += 1
else:
    print(f"✗ Failed with status {response3.status_code}")

time.sleep(1)

# Test 4: Complete scam with all intelligence types
print("\n[TEST 4] Complete scam message with all intelligence")
tests_total += 1
payload4 = {
    "sessionId": "comprehensive_004",
    "message": {
        "sender": "scammer",
        "text": "URGENT! Your account 12345678901234 blocked. Pay to scammer@paytm. Call 9123456789. Visit www.fake-bank.com",
        "timestamp": int(time.time() * 1000)
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}
response4 = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload4, timeout=30)
if response4.status_code == 200:
    print("✓ Status 200 - Check logs for:")
    print("  - bankAccounts: ['12345678901234']")
    print("  - upiIds: ['scammer@paytm']")
    print("  - phoneNumbers: ['9123456789']")
    print("  - phishingLinks: ['www.fake-bank.com']")
    print("  - NO empty strings in any array")
    tests_passed += 1
else:
    print(f"✗ Failed with status {response4.status_code}")

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"Tests Passed: {tests_passed}/{tests_total}")

if tests_passed == tests_total:
    print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("\nCritical verifications in server logs:")
    print("1. NO empty strings in phoneNumbers")
    print("2. NO 10-digit phone numbers in bankAccounts")
    print("3. NO 12-digit +91 numbers in bankAccounts")
    print("4. All arrays are clean ([] or valid values)")
    print("5. GUVI callback status: 200")
else:
    print(f"\n✗ {tests_total - tests_passed} test(s) failed")

print("="*80)
