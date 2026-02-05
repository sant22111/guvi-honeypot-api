import os
import re
import json
import requests
from typing import Optional, List
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GUVI Honeypot Scam Detection API")

# In-memory session storage
session_store = defaultdict(lambda: {
    "messages": [],
    "scam_detected": False,
    "intelligence": {
        "bankAccounts": [],
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "suspiciousKeywords": []
    },
    "callback_sent": False
})

# Scam detection keywords (GUVI required)
SCAM_KEYWORDS = [
    "otp", "kyc", "urgent", "blocked", "verify", "loan", "prize", 
    "reward", "parcel", "courier", "refund", "upi", "payment", 
    "bank", "account", "suspend"
]

# Regex patterns for intelligence extraction
UPI_PATTERN = re.compile(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b')
URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)
BANK_ACCOUNT_PATTERN = re.compile(r'\b[0-9]{9,18}\b')
PHONE_PATTERN = re.compile(r'(?:\+91[-\s]?)?[6-9]\d{9}\b')

# GUVI Pydantic Models
class Message(BaseModel):
    sender: str
    text: str
    timestamp: int

class Metadata(BaseModel):
    channel: str
    language: str
    locale: str

class GUVIRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message]
    metadata: Metadata

class GUVIResponse(BaseModel):
    status: str
    reply: str

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str]
    upiIds: List[str]
    phishingLinks: List[str]
    phoneNumbers: List[str]
    suspiciousKeywords: List[str]

class GUVICallbackPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str

def check_scam_patterns(text: str) -> tuple[bool, List[str]]:
    """Check if text contains scam patterns and return detected keywords"""
    text_lower = text.lower()
    detected_keywords = []
    
    for keyword in SCAM_KEYWORDS:
        if keyword in text_lower:
            detected_keywords.append(keyword)
    
    has_url = bool(URL_PATTERN.search(text))
    if has_url:
        detected_keywords.append("suspicious_link")
    
    is_scam = len(detected_keywords) > 0
    return is_scam, detected_keywords

def extract_intelligence(text: str) -> dict:
    """Extract intelligence from text"""
    upi_ids = list(set(UPI_PATTERN.findall(text)))
    phishing_links = list(set(URL_PATTERN.findall(text)))
    bank_accounts = list(set(BANK_ACCOUNT_PATTERN.findall(text)))
    phone_numbers = list(set(PHONE_PATTERN.findall(text)))
    
    # Clean phone numbers - remove empty strings
    phone_numbers = [p.strip() for p in phone_numbers if p and p.strip()]
    
    # Remove duplicates and normalize phone numbers
    normalized_phones = []
    seen_phones = set()
    for phone in phone_numbers:
        # Remove +91, spaces, hyphens for comparison
        normalized = phone.replace('+91', '').replace('-', '').replace(' ', '')
        if normalized and len(normalized) == 10 and normalized not in seen_phones:
            normalized_phones.append(normalized)
            seen_phones.add(normalized)
    
    # Filter out phone numbers from bank accounts
    # Exclude: 10-digit numbers (phones) and 12-digit numbers starting with 91 (phones with +91)
    phone_set = set(normalized_phones)
    bank_accounts_filtered = []
    for acc in bank_accounts:
        # Skip if it's a 10-digit phone number
        if len(acc) == 10 and acc in phone_set:
            continue
        # Skip if it's a 12-digit number starting with 91 (likely +91 phone)
        if len(acc) == 12 and acc.startswith('91') and acc[2:] in phone_set:
            continue
        # Keep if it's a real bank account (11, 13-18 digits)
        if len(acc) >= 11 and len(acc) != 12:
            bank_accounts_filtered.append(acc)
    
    return {
        "bankAccounts": bank_accounts_filtered,
        "upiIds": upi_ids,
        "phishingLinks": phishing_links,
        "phoneNumbers": normalized_phones
    }

def generate_honeypot_reply(message_text: str, conversation_history: List[Message], language: str) -> str:
    """Generate honeypot reply using Grok API with fallback"""
    
    # Try Grok API if available
    xai_api_key = os.getenv("XAI_API_KEY")
    if xai_api_key and xai_api_key.startswith("xai-"):
        try:
            # Build conversation context
            context = ""
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                context += f"{msg.sender}: {msg.text}\n"
            context += f"scammer: {message_text}\n"
            
            system_prompt = """You are an ethical scam honeypot agent acting as a normal worried Indian user. 
Your goal is to keep the scammer engaged and extract information like UPI IDs, bank details, phone numbers, and phishing links.
NEVER share OTP, PIN, CVV, password or confirm sending money. Act confused and ask clarifying questions.
Respond naturally in a conversational tone."""
            
            user_prompt = f"""Conversation so far:
{context}

Generate a natural reply that:
1. Shows concern/worry about the situation
2. Asks for more details (UPI ID, bank name, phone number, official link)
3. Sounds like a real person, not a bot
4. Does NOT reveal you know it's a scam

Language: {language}
Reply:"""
            
            # Use requests library directly to avoid OpenAI client issues
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {xai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": os.getenv("XAI_MODEL", "grok-3"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply
            else:
                print(f"Grok API error: Status {response.status_code}")
            
        except Exception as e:
            print(f"Grok API error: {e}")
            # Fall through to fallback
    
    # Fallback reply templates
    fallback_replies = [
        "Oh no 😟 why will my account be blocked? Can you tell me which bank this is from? Please share the official link and UPI ID again.",
        "I'm really worried about this. Can you give me more details? Which bank account should I use? Do you have a phone number I can call?",
        "This is urgent? What should I do? Can you send me the exact UPI ID or payment link? I want to make sure I'm doing this correctly.",
        "I don't understand. Can you explain what happened to my account? Is there a customer care number I can contact? What's the UPI ID for payment?"
    ]
    
    # Simple selection based on message length
    import hashlib
    hash_val = int(hashlib.md5(message_text.encode()).hexdigest(), 16)
    return fallback_replies[hash_val % len(fallback_replies)]

def send_guvi_callback(session_id: str, session_data: dict):
    """Send final result to GUVI callback endpoint"""
    try:
        # Calculate total messages
        total_messages = len(session_data["messages"])
        
        # Generate agent notes
        intel = session_data["intelligence"]
        notes_parts = []
        if intel["upiIds"]:
            notes_parts.append(f"Extracted {len(intel['upiIds'])} UPI IDs")
        if intel["bankAccounts"]:
            notes_parts.append(f"{len(intel['bankAccounts'])} bank accounts")
        if intel["phishingLinks"]:
            notes_parts.append(f"{len(intel['phishingLinks'])} phishing links")
        if intel["phoneNumbers"]:
            notes_parts.append(f"{len(intel['phoneNumbers'])} phone numbers")
        
        agent_notes = "Scam detected. " + ", ".join(notes_parts) if notes_parts else "Scam detected with suspicious keywords."
        
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": total_messages,
            "extractedIntelligence": intel,
            "agentNotes": agent_notes
        }
        
        print(f"\n{'='*80}")
        print(f"[GUVI CALLBACK] SENDING for session: {session_id}")
        print(f"{'='*80}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
            json=payload,
            timeout=5,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n[GUVI CALLBACK] RESPONSE:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Text: {response.text}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"{'='*80}\n")
        
        if response.status_code in [200, 201]:
            print(f"[SUCCESS] GUVI callback succeeded for session {session_id}")
            return True
        else:
            print(f"[WARNING] GUVI callback returned non-success status: {response.status_code}")
            return False
        
    except requests.exceptions.Timeout:
        print(f"[ERROR] GUVI callback TIMEOUT for session {session_id} (5 seconds)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] GUVI callback CONNECTION ERROR for session {session_id}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] GUVI callback FAILED for session {session_id}: {type(e).__name__}: {e}")
        return False

@app.post("/honeypot/analyze", response_model=GUVIResponse)
async def analyze_message(
    request: GUVIRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Main GUVI-compliant honeypot endpoint"""
    
    # Validate API key
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Invalid API key"}
        )
    
    try:
        session_id = request.sessionId
        message_text = request.message.text
        conversation_history = request.conversationHistory
        language = request.metadata.language
        
        # Get session data
        session = session_store[session_id]
        
        # Store incoming message
        session["messages"].append({
            "sender": request.message.sender,
            "text": message_text,
            "timestamp": request.message.timestamp
        })
        
        # Check for scam patterns
        is_scam, detected_keywords = check_scam_patterns(message_text)
        
        if is_scam:
            session["scam_detected"] = True
            
            # Add detected keywords to intelligence
            for keyword in detected_keywords:
                if keyword not in session["intelligence"]["suspiciousKeywords"]:
                    session["intelligence"]["suspiciousKeywords"].append(keyword)
            
            # Extract intelligence from current message
            intel = extract_intelligence(message_text)
            
            # Merge with session intelligence
            for key in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers"]:
                for item in intel[key]:
                    if item not in session["intelligence"][key]:
                        session["intelligence"][key].append(item)
            
            # Generate honeypot reply
            reply = generate_honeypot_reply(message_text, conversation_history, language)
            
            # Extract intelligence from agent reply too
            reply_intel = extract_intelligence(reply)
            for key in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers"]:
                for item in reply_intel[key]:
                    if item not in session["intelligence"][key]:
                        session["intelligence"][key].append(item)
            
            # Store agent reply
            session["messages"].append({
                "sender": "agent",
                "text": reply,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            
            # Check if we should send GUVI callback
            has_intelligence = any([
                session["intelligence"]["bankAccounts"],
                session["intelligence"]["upiIds"],
                session["intelligence"]["phishingLinks"],
                session["intelligence"]["phoneNumbers"]
            ])
            
            if has_intelligence and not session["callback_sent"]:
                callback_success = send_guvi_callback(session_id, session)
                if callback_success:
                    session["callback_sent"] = True
            
            return GUVIResponse(status="success", reply=reply)
        
        else:
            # Not a scam - generate normal response
            normal_replies = [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Hey! Is there something you need?",
                "Hello! What's on your mind?"
            ]
            
            import hashlib
            hash_val = int(hashlib.md5(message_text.encode()).hexdigest(), 16)
            reply = normal_replies[hash_val % len(normal_replies)]
            
            # Store agent reply
            session["messages"].append({
                "sender": "agent",
                "text": reply,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            
            return GUVIResponse(status="success", reply=reply)
    
    except Exception as e:
        print(f"Error processing request: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Malformed request"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "GUVI Honeypot Scam Detection API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "analyze": "POST /honeypot/analyze",
            "health": "GET /health"
        },
        "guvi_compliant": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
