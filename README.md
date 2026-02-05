# Honeypot Scam Detection API

FastAPI backend for detecting and analyzing scam messages using rule-based detection and OpenAI-powered honeypot responses.

## Features

- **Rule-based scam detection** using keywords and URL patterns
- **AI-powered honeypot agent** that engages scammers to extract intelligence
- **Intelligence extraction** for UPI IDs, bank accounts, and phishing links
- **API key authentication** for secure access
- **Multi-language support** (English, Hindi, Tamil, Telugu, Malayalam)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
API_KEY=your-secret-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /honeypot/analyze

Analyzes a message for scam patterns and generates honeypot responses.

**Headers:**
```
x-api-key: your-secret-api-key-here
```

**Request Body:**
```json
{
  "conversation_id": "conv_12345",
  "message": "Your account has been blocked. Click here to verify KYC: www.fake-bank.com",
  "language": "en"
}
```

**Response (Scam Detected):**
```json
{
  "is_scam": true,
  "scam_type": "Phishing/KYC Scam",
  "confidence": 0.95,
  "agent_reply": "Oh no! My account is blocked? I'm very worried. What do I need to do? Should I click that link?",
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "phishing_links": ["www.fake-bank.com"]
  },
  "explanation": "Message contains KYC-related phishing attempt with suspicious URL"
}
```

**Response (No Scam):**
```json
{
  "is_scam": false,
  "scam_type": "Not Scam",
  "confidence": 0.2,
  "agent_reply": "",
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "phishing_links": []
  },
  "explanation": "No scam patterns detected"
}
```

## Scam Detection Logic

1. **Rule-based detection** checks for:
   - Keywords: otp, kyc, urgent, blocked, prize, reward, loan, courier, parcel, refund, payment, upi, collect
   - URLs (http, https, www)

2. **If scam detected:**
   - Calls OpenAI API to generate contextual honeypot response
   - Extracts intelligence (UPI IDs, bank accounts, phishing links)
   - Returns detailed analysis

3. **If no scam:**
   - Returns low confidence "Not Scam" response

## Error Responses

**401 Unauthorized:**
```json
{
  "error": "Unauthorized"
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid language. Must be one of: en, hi, ta, te, ml"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "OpenAI API error: ..."
}
```

## Development

Run with auto-reload for development:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Security Notes

- Never commit `.env` file to version control
- Keep your API keys secure
- The honeypot agent never shares sensitive information (OTP, PIN, CVV, passwords)
- Always validate and sanitize user inputs
