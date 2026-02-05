#!/bin/bash

# GUVI Honeypot API - cURL Test Commands

API_URL="http://localhost:8000"
API_KEY="your-0002121"

echo "=================================="
echo "GUVI HONEYPOT API - cURL TESTS"
echo "=================================="

echo -e "\n1. Test Scam Detection"
curl -X POST "$API_URL/honeypot/analyze" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "sessionId": "curl_test_001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Your bank account blocked. Pay to scammer@paytm or call 9876543210",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'

echo -e "\n\n2. Test Legitimate Message"
curl -X POST "$API_URL/honeypot/analyze" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "sessionId": "curl_test_002",
    "message": {
      "sender": "scammer",
      "text": "Hello, how are you?",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'

echo -e "\n\n3. Test Multi-Turn Conversation"
curl -X POST "$API_URL/honeypot/analyze" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
    "sessionId": "curl_test_003",
    "message": {
      "sender": "scammer",
      "text": "Pay Rs 100 to verify@paytm to activate account",
      "timestamp": 1770005529000
    },
    "conversationHistory": [
      {
        "sender": "scammer",
        "text": "Your KYC expired",
        "timestamp": 1770005528000
      },
      {
        "sender": "user",
        "text": "Which bank is this?",
        "timestamp": 1770005528500
      }
    ],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'

echo -e "\n\n4. Test Authentication Failure"
curl -X POST "$API_URL/honeypot/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "curl_test_004",
    "message": {
      "sender": "scammer",
      "text": "Test",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'

echo -e "\n\n5. Test Health Check"
curl -X GET "$API_URL/health"

echo -e "\n\n=================================="
echo "Tests Complete!"
echo "=================================="
