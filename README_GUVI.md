# GUVI Honeypot Scam Detection API

FastAPI-based honeypot system compliant with **GUVI Hackathon Problem Statement 2**.

## Features

✅ **GUVI-Compliant Request/Response Format**
✅ **Scam Detection** with keyword and URL pattern matching
✅ **Agentic Honeypot Replies** using Grok AI (with fallback)
✅ **Intelligence Extraction** (UPI IDs, bank accounts, phone numbers, phishing links)
✅ **Automatic GUVI Callback** to `updateHoneyPotFinalResult` endpoint
✅ **Session-Based Conversation Tracking**
✅ **API Key Authentication**

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
API_KEY=your-secret-api-key-here
XAI_API_KEY=YOUR_XAI_KEY_HERE
XAI_MODEL=grok-3
```

**Required:**
- `API_KEY` - Your secret API key for authentication (generate a strong random key)

**Optional (for AI-powered replies):**
- `XAI_API_KEY` - Grok API key from x.ai (get from https://console.x.ai)
- `XAI_MODEL` - Model name (default: grok-3)

If Grok API is not available, the system uses fallback template replies.

### 3. Run the Server

```bash
uvicorn main_guvi:app --host 0.0.0.0 --port 8000
```

Or:

```bash
python main_guvi.py
```

Server will start at: `http://localhost:8000`

---

## API Endpoints

### Main Endpoint

**POST** `/honeypot/analyze`

Analyzes incoming messages for scam patterns and generates honeypot replies.

**Headers:**
```
x-api-key: your-secret-api-key-here
```

**Request Body (GUVI Format):**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your account is blocked. Send OTP to verify.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Previous message",
      "timestamp": 1770005528000
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response (GUVI Format):**
```json
{
  "status": "success",
  "reply": "Oh no! Why is my account blocked? Can you tell me which bank this is from? Please share the official link and UPI ID."
}
```

### Health Check

**GET** `/health`

```json
{
  "status": "healthy"
}
```

---

## Testing

Run the test suite:

```bash
python test_guvi.py
```

### Manual cURL Test

```bash
curl -X POST http://localhost:8000/honeypot/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-api-key-here" \
  -d '{
    "sessionId": "test_001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Your bank account blocked. Pay to scammer@paytm",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

---

## How It Works

### 1. Scam Detection

The system checks for:
- **Keywords:** otp, kyc, urgent, blocked, verify, loan, prize, reward, parcel, courier, refund, upi, payment, bank, account, suspend
- **URLs:** Any http/https or www links

If any keyword or URL is found → `scamDetected = true`

### 2. Intelligence Extraction

Extracts using regex patterns:
- **UPI IDs:** `username@bankname`
- **Bank Accounts:** 9-18 digit numbers
- **Phone Numbers:** Indian mobile numbers (+91 or 10-digit)
- **Phishing Links:** URLs in the message
- **Suspicious Keywords:** Detected scam keywords

### 3. Honeypot Reply Generation

**With Grok AI (if API key provided):**
- Generates contextual, natural-sounding replies
- Acts as a worried Indian user
- Asks questions to extract more intelligence
- Never shares OTP/PIN/CVV or confirms payments

**Fallback (if Grok unavailable):**
- Uses pre-defined template replies
- Still sounds natural and engaging

### 4. GUVI Callback

When scam is detected AND intelligence is extracted, the system automatically sends a callback to:

**Endpoint:** `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`

**Payload:**
```json
{
  "sessionId": "test_001",
  "scamDetected": true,
  "totalMessagesExchanged": 3,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["www.fake-bank.com"],
    "phoneNumbers": ["9876543210"],
    "suspiciousKeywords": ["urgent", "blocked", "otp"]
  },
  "agentNotes": "Scam detected. Extracted 1 UPI IDs, 1 phishing links, 1 phone numbers"
}
```

**Important:** Callback is sent only **once per sessionId** to avoid duplicates.

---

## Session Management

The system maintains in-memory session storage:

```python
{
  "session_id_123": {
    "messages": [...],           # All conversation messages
    "scam_detected": true,       # Whether scam was detected
    "intelligence": {...},       # Extracted intelligence
    "callback_sent": false       # Whether GUVI callback was sent
  }
}
```

This enables:
- Multi-turn conversation tracking
- Cumulative intelligence extraction
- One-time callback per session

---

## Error Handling

### 401 Unauthorized
```json
{
  "status": "error",
  "message": "Invalid API key"
}
```

### 400 Bad Request
```json
{
  "status": "error",
  "message": "Malformed request"
}
```

### Graceful Degradation
- If Grok API fails → Uses fallback replies
- If GUVI callback fails → Logs error but continues serving requests
- System never crashes, always returns a reply

---

## Architecture

```
┌─────────────────┐
│  GUVI Request   │
│  (sessionId,    │
│   message, etc) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ API Key Auth    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scam Detection  │
│ (Keywords/URLs) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ Scam  │ │ Normal   │
│ Flow  │ │ Reply    │
└───┬───┘ └────┬─────┘
    │          │
    ▼          │
┌─────────────────┐
│ Intelligence    │
│ Extraction      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Grok AI Reply   │
│ (with fallback) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store in        │
│ Session         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GUVI Callback   │
│ (if conditions  │
│  met)           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Reply    │
│ to Client       │
└─────────────────┘
```

---

## Production Deployment

### Environment Setup
1. Set strong `API_KEY` in production
2. Configure `XAI_API_KEY` for AI-powered replies
3. Use process manager (PM2, systemd, supervisor)
4. Set up reverse proxy (nginx, Caddy)
5. Enable HTTPS

### Scaling Considerations
- Current: In-memory session storage
- Production: Use Redis for session storage
- Load balancing: Multiple instances with shared Redis

### Monitoring
- Check `/health` endpoint
- Monitor GUVI callback success rate
- Track scam detection accuracy
- Log intelligence extraction metrics

---

## GUVI Compliance Checklist

✅ Accepts GUVI request format (sessionId, message, conversationHistory, metadata)
✅ Returns GUVI response format (status, reply)
✅ Detects scam intent using keywords and URLs
✅ Generates agentic honeypot replies
✅ Extracts intelligence (UPI, bank accounts, links, phones, keywords)
✅ Sends callback to `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`
✅ Requires API key authentication
✅ Returns 401 for invalid API key
✅ Returns 400 for malformed requests
✅ Never crashes (graceful error handling)
✅ Health check endpoint available

---

## Support

For issues or questions:
1. Check server logs
2. Verify environment variables
3. Test with provided test suite
4. Review API documentation at `/docs`

---

## License

MIT License - Built for GUVI Hackathon Problem Statement 2
