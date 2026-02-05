import os
import re
import json
from typing import Optional, List
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Honeypot Scam Detection API")

# In-memory conversation storage (use database in production)
conversation_history = defaultdict(list)
scam_statistics = {
    "total_analyzed": 0,
    "scams_detected": 0,
    "scam_types": defaultdict(int),
    "intelligence_collected": {
        "upi_ids": set(),
        "bank_accounts": set(),
        "phishing_links": set(),
        "phone_numbers": set(),
        "emails": set()
    }
}

SCAM_KEYWORDS = [
    "otp", "kyc", "urgent", "blocked", "prize", "reward", 
    "loan", "courier", "parcel", "refund", "payment", "upi", "collect"
]

URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)
UPI_PATTERN = re.compile(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b')
BANK_ACCOUNT_PATTERN = re.compile(r'\b[0-9]{9,18}\b')
IFSC_PATTERN = re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+91|0)?[6-9]\d{9}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
CRYPTO_PATTERN = re.compile(r'\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b')

# Evidence signal keywords
URGENT_KEYWORDS = ["urgent", "immediately", "now", "asap", "hurry", "quick", "expire", "limited time"]
IMPERSONATION_KEYWORDS = ["bank", "government", "police", "officer", "manager", "support", "helpdesk"]
PAYMENT_KEYWORDS = ["pay", "send money", "transfer", "upi", "payment", "amount", "rupees", "rs"]
CREDENTIAL_KEYWORDS = ["otp", "password", "pin", "cvv", "kyc", "verify", "confirm", "authenticate"]

class AnalyzeRequest(BaseModel):
    conversation_id: str
    message: str
    language: str

class Message(BaseModel):
    role: str
    content: str

class MultiTurnRequest(BaseModel):
    conversation_id: str
    messages: List[Message]
    language: str

class ExtractedIntelligence(BaseModel):
    upi_ids: list[str]
    bank_accounts: list[str]
    ifsc_codes: list[str]
    phishing_links: list[str]
    phone_numbers: list[str]
    emails: list[str]
    crypto_wallets: list[str]

class AnalyzeResponse(BaseModel):
    is_scam: bool
    scam_category: str
    scam_subtype: str
    confidence: float
    risk_score: int
    agent_reply: str
    extracted_intelligence: ExtractedIntelligence
    signals_detected: list[str]
    explanation: str
    conversation_turn: int

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[dict]
    total_turns: int
    scam_detected: bool
    total_intelligence: ExtractedIntelligence

class ScamStatistics(BaseModel):
    total_analyzed: int
    scams_detected: int
    detection_rate: float
    scam_types: dict
    top_scam_type: str
    total_intelligence_collected: dict

def check_scam_patterns(message: str) -> bool:
    message_lower = message.lower()
    
    for keyword in SCAM_KEYWORDS:
        if keyword in message_lower:
            return True
    
    if URL_PATTERN.search(message):
        return True
    
    return False

def extract_intelligence(text: str) -> ExtractedIntelligence:
    upi_ids = list(set(UPI_PATTERN.findall(text)))
    bank_accounts = list(set(BANK_ACCOUNT_PATTERN.findall(text)))
    ifsc_codes = list(set(IFSC_PATTERN.findall(text)))
    phishing_links = list(set(URL_PATTERN.findall(text)))
    phone_numbers = list(set(PHONE_PATTERN.findall(text)))
    emails = list(set(EMAIL_PATTERN.findall(text)))
    crypto_wallets = list(set(CRYPTO_PATTERN.findall(text)))
    
    # Filter out UPI IDs from emails
    emails = [e for e in emails if e not in upi_ids]
    
    return ExtractedIntelligence(
        upi_ids=upi_ids,
        bank_accounts=bank_accounts,
        ifsc_codes=ifsc_codes,
        phishing_links=phishing_links,
        phone_numbers=phone_numbers,
        emails=emails,
        crypto_wallets=crypto_wallets
    )

def detect_evidence_signals(message: str) -> list[str]:
    """Detect evidence signals in the message"""
    signals = []
    message_lower = message.lower()
    
    if any(word in message_lower for word in URGENT_KEYWORDS):
        signals.append("URGENT_LANGUAGE")
    
    if any(word in message_lower for word in IMPERSONATION_KEYWORDS):
        signals.append("IMPERSONATION_ATTEMPT")
    
    if any(word in message_lower for word in PAYMENT_KEYWORDS):
        signals.append("PAYMENT_REQUEST")
    
    if any(word in message_lower for word in CREDENTIAL_KEYWORDS):
        signals.append("CREDENTIAL_REQUEST")
    
    if URL_PATTERN.search(message):
        signals.append("SUSPICIOUS_LINK")
    
    if UPI_PATTERN.search(message):
        signals.append("UPI_ID_PRESENT")
    
    if PHONE_PATTERN.search(message):
        signals.append("PHONE_NUMBER_PRESENT")
    
    return signals

def categorize_scam(scam_type: str) -> tuple[str, str]:
    """Categorize scam into category and subtype"""
    scam_taxonomy = {
        "KYC Fraud": ("BANKING_FRAUD", "KYC_VERIFICATION_SCAM"),
        "OTP Scam": ("BANKING_FRAUD", "OTP_PHISHING_SCAM"),
        "Loan Scam": ("FINANCIAL_FRAUD", "INSTANT_LOAN_SCAM"),
        "Prize Scam": ("LOTTERY_FRAUD", "FAKE_PRIZE_SCAM"),
        "Courier Scam": ("DELIVERY_FRAUD", "FAKE_COURIER_SCAM"),
        "Investment Scam": ("FINANCIAL_FRAUD", "INVESTMENT_PONZI_SCAM"),
        "UPI Collect Scam": ("BANKING_FRAUD", "UPI_COLLECT_FRAUD"),
        "Impersonation Scam": ("IDENTITY_FRAUD", "AUTHORITY_IMPERSONATION"),
        "Other": ("UNKNOWN_FRAUD", "UNCLASSIFIED_SCAM"),
        "Not Scam": ("NOT_SCAM", "LEGITIMATE_MESSAGE")
    }
    
    return scam_taxonomy.get(scam_type, ("UNKNOWN_FRAUD", "UNCLASSIFIED_SCAM"))

def calculate_risk_score(scam_type: str, confidence: float, intelligence: ExtractedIntelligence) -> int:
    """Calculate risk score 0-100 based on scam characteristics"""
    base_score = int(confidence * 50)
    
    # Add points for extracted intelligence
    intel_score = 0
    intel_score += len(intelligence.upi_ids) * 10
    intel_score += len(intelligence.bank_accounts) * 15
    intel_score += len(intelligence.phishing_links) * 8
    intel_score += len(intelligence.phone_numbers) * 5
    intel_score += len(intelligence.emails) * 5
    intel_score += len(intelligence.crypto_wallets) * 12
    
    # High-risk scam types get bonus
    high_risk_types = ["KYC Fraud", "OTP Scam", "Investment Scam"]
    if scam_type in high_risk_types:
        base_score += 10
    
    total_score = min(base_score + intel_score, 100)
    return total_score

def update_statistics(is_scam: bool, scam_type: str, intelligence: ExtractedIntelligence):
    """Update global scam statistics"""
    scam_statistics["total_analyzed"] += 1
    
    if is_scam:
        scam_statistics["scams_detected"] += 1
        scam_statistics["scam_types"][scam_type] += 1
        
        # Collect intelligence
        scam_statistics["intelligence_collected"]["upi_ids"].update(intelligence.upi_ids)
        scam_statistics["intelligence_collected"]["bank_accounts"].update(intelligence.bank_accounts)
        scam_statistics["intelligence_collected"]["phishing_links"].update(intelligence.phishing_links)
        scam_statistics["intelligence_collected"]["phone_numbers"].update(intelligence.phone_numbers)
        scam_statistics["intelligence_collected"]["emails"].update(intelligence.emails)

async def get_grok_analysis(message: str, language: str) -> dict:
    try:
        client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )
        
        system_prompt = "You are an ethical scam honeypot agent. Act like a normal Indian user. Be worried and confused. Ask questions to extract UPI IDs, bank details and phishing links. Never share OTP, PIN, CVV, password or send money. Output JSON only."
        
        user_prompt = f"""
Message: {message}
Language: {language}

Return ONLY valid JSON in this exact schema:
{{
  "scam_type": "KYC Fraud | OTP Scam | Loan Scam | Prize Scam | Courier Scam | Investment Scam | UPI Collect Scam | Impersonation Scam | Other",
  "confidence": 0.0,
  "agent_reply": "string",
  "explanation": "string"
}}
"""
        
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            return {
                "scam_type": "OTP Scam",
                "confidence": 0.85,
                "agent_reply": "Oh no! My account is blocked? I'm very worried. What should I do? Do I need to click that link?",
                "explanation": "Message contains scam keywords and suspicious patterns. (Note: AI quota exceeded, using fallback response)"
            }
        raise HTTPException(status_code=500, detail=f"Grok API error: {error_msg}")

@app.post("/honeypot/analyze", response_model=AnalyzeResponse)
async def analyze_message(
    request: AnalyzeRequest,
    x_api_key: Optional[str] = Header(None)
):
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if request.language not in ["en", "hi", "ta", "te", "ml"]:
        raise HTTPException(status_code=400, detail="Invalid language. Must be one of: en, hi, ta, te, ml")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    is_scam = check_scam_patterns(request.message)
    
    if not is_scam:
        return AnalyzeResponse(
            is_scam=False,
            scam_category="NOT_SCAM",
            scam_subtype="LEGITIMATE_MESSAGE",
            confidence=0.2,
            risk_score=0,
            agent_reply="",
            extracted_intelligence=ExtractedIntelligence(
                upi_ids=[],
                bank_accounts=[],
                ifsc_codes=[],
                phishing_links=[],
                phone_numbers=[],
                emails=[],
                crypto_wallets=[]
            ),
            signals_detected=[],
            explanation="No scam patterns detected",
            conversation_turn=len(conversation_history[request.conversation_id]) + 1
        )
    
    grok_result = await get_grok_analysis(request.message, request.language)
    
    combined_text = request.message + " " + grok_result.get("agent_reply", "")
    intelligence = extract_intelligence(combined_text)
    signals = detect_evidence_signals(request.message)
    
    scam_type = grok_result.get("scam_type") or "Other"
    confidence = float(grok_result.get("confidence", 0.8))
    confidence = max(0.0, min(1.0, confidence))
    
    scam_category, scam_subtype = categorize_scam(scam_type)
    risk_score = calculate_risk_score(scam_type, confidence, intelligence)
    
    # Store conversation history
    conversation_history[request.conversation_id].append({
        "timestamp": datetime.now().isoformat(),
        "message": request.message,
        "agent_reply": grok_result.get("agent_reply", ""),
        "scam_type": scam_type,
        "scam_category": scam_category,
        "scam_subtype": scam_subtype,
        "confidence": confidence,
        "risk_score": risk_score,
        "signals": signals,
        "intelligence": intelligence.dict()
    })
    
    # Update statistics
    update_statistics(True, scam_type, intelligence)
    
    return AnalyzeResponse(
        is_scam=True,
        scam_category=scam_category,
        scam_subtype=scam_subtype,
        confidence=confidence,
        risk_score=risk_score,
        agent_reply=grok_result.get("agent_reply", ""),
        extracted_intelligence=intelligence,
        signals_detected=signals,
        explanation=grok_result.get("explanation", "Scam detected based on patterns"),
        conversation_turn=len(conversation_history[request.conversation_id])
    )

@app.post("/honeypot/respond", response_model=AnalyzeResponse)
async def multi_turn_respond(
    request: MultiTurnRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Multi-turn conversation endpoint - analyzes full conversation and generates next agent reply"""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    # Build full conversation context
    conversation_text = ""
    for msg in request.messages:
        conversation_text += f"{msg.role}: {msg.content}\n"
    
    # Get latest scammer message
    latest_message = request.messages[-1].content if request.messages else ""
    
    # Check if scam patterns exist in conversation
    is_scam = check_scam_patterns(conversation_text)
    
    if not is_scam:
        return AnalyzeResponse(
            is_scam=False,
            scam_category="NOT_SCAM",
            scam_subtype="LEGITIMATE_MESSAGE",
            confidence=0.2,
            risk_score=0,
            agent_reply="",
            extracted_intelligence=ExtractedIntelligence(
                upi_ids=[],
                bank_accounts=[],
                ifsc_codes=[],
                phishing_links=[],
                phone_numbers=[],
                emails=[],
                crypto_wallets=[]
            ),
            signals_detected=[],
            explanation="No scam patterns detected in conversation",
            conversation_turn=len(request.messages)
        )
    
    # Use Grok to analyze with full context
    try:
        client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )
        
        system_prompt = "You are an ethical scam honeypot agent. Act like a normal Indian user. Be worried and confused. Ask questions to extract UPI IDs, bank details and phishing links. Never share OTP, PIN, CVV, password or send money. Output JSON only."
        
        user_prompt = f"""
Full conversation so far:
{conversation_text}

Language: {request.language}

Based on this conversation, generate the next agent reply to keep the scammer engaged and extract more intelligence.

Return ONLY valid JSON in this exact schema:
{{
  "scam_type": "KYC Fraud | OTP Scam | Loan Scam | Prize Scam | Courier Scam | Investment Scam | UPI Collect Scam | Impersonation Scam | Other",
  "confidence": 0.0,
  "agent_reply": "string",
  "explanation": "string"
}}
"""
        
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        grok_result = json.loads(result_text)
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            grok_result = {
                "scam_type": "OTP Scam",
                "confidence": 0.85,
                "agent_reply": "I'm worried. Can you tell me more details? What should I do next?",
                "explanation": "Multi-turn scam conversation detected. (Note: AI quota exceeded, using fallback response)"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Grok API error: {error_msg}")
    
    # Extract intelligence from entire conversation
    combined_text = conversation_text + " " + grok_result.get("agent_reply", "")
    intelligence = extract_intelligence(combined_text)
    signals = detect_evidence_signals(latest_message)
    
    scam_type = grok_result.get("scam_type") or "Other"
    confidence = float(grok_result.get("confidence", 0.8))
    confidence = max(0.0, min(1.0, confidence))
    
    scam_category, scam_subtype = categorize_scam(scam_type)
    risk_score = calculate_risk_score(scam_type, confidence, intelligence)
    
    # Store in conversation history
    for msg in request.messages:
        if msg.role == "scammer":
            conversation_history[request.conversation_id].append({
                "timestamp": datetime.now().isoformat(),
                "message": msg.content,
                "agent_reply": "",
                "scam_type": scam_type,
                "scam_category": scam_category,
                "scam_subtype": scam_subtype,
                "confidence": confidence,
                "risk_score": risk_score,
                "signals": signals,
                "intelligence": {}
            })
    
    # Store agent reply
    conversation_history[request.conversation_id].append({
        "timestamp": datetime.now().isoformat(),
        "message": "",
        "agent_reply": grok_result.get("agent_reply", ""),
        "scam_type": scam_type,
        "scam_category": scam_category,
        "scam_subtype": scam_subtype,
        "confidence": confidence,
        "risk_score": risk_score,
        "signals": signals,
        "intelligence": intelligence.dict()
    })
    
    # Update statistics
    update_statistics(True, scam_type, intelligence)
    
    return AnalyzeResponse(
        is_scam=True,
        scam_category=scam_category,
        scam_subtype=scam_subtype,
        confidence=confidence,
        risk_score=risk_score,
        agent_reply=grok_result.get("agent_reply", ""),
        extracted_intelligence=intelligence,
        signals_detected=signals,
        explanation=grok_result.get("explanation", "Multi-turn scam conversation detected"),
        conversation_turn=len(request.messages)
    )

@app.get("/conversation/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str, x_api_key: Optional[str] = Header(None)):
    """Get full conversation history for a specific conversation ID"""
    api_key = os.getenv("API_KEY")
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if conversation_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = conversation_history[conversation_id]
    
    # Aggregate all intelligence from conversation
    all_intelligence = ExtractedIntelligence(
        upi_ids=[],
        bank_accounts=[],
        ifsc_codes=[],
        phishing_links=[],
        phone_numbers=[],
        emails=[],
        crypto_wallets=[]
    )
    
    for msg in messages:
        intel = msg.get("intelligence", {})
        all_intelligence.upi_ids.extend(intel.get("upi_ids", []))
        all_intelligence.bank_accounts.extend(intel.get("bank_accounts", []))
        all_intelligence.ifsc_codes.extend(intel.get("ifsc_codes", []))
        all_intelligence.phishing_links.extend(intel.get("phishing_links", []))
        all_intelligence.phone_numbers.extend(intel.get("phone_numbers", []))
        all_intelligence.emails.extend(intel.get("emails", []))
        all_intelligence.crypto_wallets.extend(intel.get("crypto_wallets", []))
    
    # Remove duplicates
    all_intelligence.upi_ids = list(set(all_intelligence.upi_ids))
    all_intelligence.bank_accounts = list(set(all_intelligence.bank_accounts))
    all_intelligence.ifsc_codes = list(set(all_intelligence.ifsc_codes))
    all_intelligence.phishing_links = list(set(all_intelligence.phishing_links))
    all_intelligence.phone_numbers = list(set(all_intelligence.phone_numbers))
    all_intelligence.emails = list(set(all_intelligence.emails))
    all_intelligence.crypto_wallets = list(set(all_intelligence.crypto_wallets))
    
    return ConversationHistory(
        conversation_id=conversation_id,
        messages=messages,
        total_turns=len(messages),
        scam_detected=any(msg.get("scam_type") != "Not Scam" for msg in messages),
        total_intelligence=all_intelligence
    )

@app.get("/analytics", response_model=ScamStatistics)
async def get_analytics(x_api_key: Optional[str] = Header(None)):
    """Get real-time scam detection analytics and statistics"""
    api_key = os.getenv("API_KEY")
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    total = scam_statistics["total_analyzed"]
    detected = scam_statistics["scams_detected"]
    detection_rate = (detected / total * 100) if total > 0 else 0.0
    
    scam_types_dict = dict(scam_statistics["scam_types"])
    top_scam = max(scam_types_dict.items(), key=lambda x: x[1])[0] if scam_types_dict else "None"
    
    return ScamStatistics(
        total_analyzed=total,
        scams_detected=detected,
        detection_rate=round(detection_rate, 2),
        scam_types=scam_types_dict,
        top_scam_type=top_scam,
        total_intelligence_collected={
            "upi_ids": len(scam_statistics["intelligence_collected"]["upi_ids"]),
            "bank_accounts": len(scam_statistics["intelligence_collected"]["bank_accounts"]),
            "phishing_links": len(scam_statistics["intelligence_collected"]["phishing_links"]),
            "phone_numbers": len(scam_statistics["intelligence_collected"]["phone_numbers"]),
            "emails": len(scam_statistics["intelligence_collected"]["emails"])
        }
    )

@app.get("/honeypot/report/{conversation_id}")
async def get_conversation_report(conversation_id: str, x_api_key: Optional[str] = Header(None)):
    """Generate formatted report for a specific conversation - law enforcement ready"""
    api_key = os.getenv("API_KEY")
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if conversation_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = conversation_history[conversation_id]
    
    # Aggregate intelligence
    all_intel = ExtractedIntelligence(
        upi_ids=[], bank_accounts=[], ifsc_codes=[], phishing_links=[],
        phone_numbers=[], emails=[], crypto_wallets=[]
    )
    
    max_risk = 0
    final_scam_type = "Unknown"
    timeline = []
    
    for msg in messages:
        intel = msg.get("intelligence", {})
        all_intel.upi_ids.extend(intel.get("upi_ids", []))
        all_intel.bank_accounts.extend(intel.get("bank_accounts", []))
        all_intel.ifsc_codes.extend(intel.get("ifsc_codes", []))
        all_intel.phishing_links.extend(intel.get("phishing_links", []))
        all_intel.phone_numbers.extend(intel.get("phone_numbers", []))
        all_intel.emails.extend(intel.get("emails", []))
        all_intel.crypto_wallets.extend(intel.get("crypto_wallets", []))
        
        risk = msg.get("risk_score", 0)
        if risk > max_risk:
            max_risk = risk
            final_scam_type = msg.get("scam_subtype", "Unknown")
        
        timeline.append({
            "timestamp": msg.get("timestamp"),
            "message": msg.get("message", ""),
            "agent_reply": msg.get("agent_reply", ""),
            "signals": msg.get("signals", []),
            "risk_score": risk
        })
    
    # Remove duplicates
    all_intel.upi_ids = list(set(all_intel.upi_ids))
    all_intel.bank_accounts = list(set(all_intel.bank_accounts))
    all_intel.ifsc_codes = list(set(all_intel.ifsc_codes))
    all_intel.phishing_links = list(set(all_intel.phishing_links))
    all_intel.phone_numbers = list(set(all_intel.phone_numbers))
    all_intel.emails = list(set(all_intel.emails))
    all_intel.crypto_wallets = list(set(all_intel.crypto_wallets))
    
    # Determine action
    if max_risk >= 80:
        action = "IMMEDIATE_BLOCK_AND_REPORT"
    elif max_risk >= 60:
        action = "REPORT_TO_AUTHORITIES"
    elif max_risk >= 40:
        action = "MONITOR_AND_FLAG"
    else:
        action = "LOW_PRIORITY_REVIEW"
    
    return {
        "report_id": f"RPT-{conversation_id}-{datetime.now().strftime('%Y%m%d')}",
        "generated_at": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "summary": {
            "total_turns": len(messages),
            "scam_type": final_scam_type,
            "max_risk_score": max_risk,
            "recommended_action": action
        },
        "timeline": timeline,
        "extracted_evidence": {
            "upi_ids": all_intel.upi_ids,
            "bank_accounts": all_intel.bank_accounts,
            "ifsc_codes": all_intel.ifsc_codes,
            "phishing_links": all_intel.phishing_links,
            "phone_numbers": all_intel.phone_numbers,
            "emails": all_intel.emails,
            "crypto_wallets": all_intel.crypto_wallets
        },
        "evidence_count": {
            "total_identifiers": len(all_intel.upi_ids) + len(all_intel.bank_accounts) + 
                                 len(all_intel.phone_numbers) + len(all_intel.emails),
            "financial_identifiers": len(all_intel.upi_ids) + len(all_intel.bank_accounts) + len(all_intel.ifsc_codes),
            "phishing_links": len(all_intel.phishing_links)
        },
        "recommended_actions": [
            "File FIR with National Cyber Crime Reporting Portal (cybercrime.gov.in)",
            "Report UPI IDs to NPCI for immediate blocking",
            "Report phishing domains to domain registrar and Google Safe Browsing",
            "Share phone numbers with telecom providers for blocking",
            "Forward evidence to local cyber crime cell",
            "Document all evidence for legal proceedings"
        ],
        "legal_notice": "This report is generated by an automated honeypot system. All evidence should be verified before legal action."
    }

@app.get("/intelligence/report")
async def get_intelligence_report(x_api_key: Optional[str] = Header(None)):
    """Get detailed intelligence report for law enforcement"""
    api_key = os.getenv("API_KEY")
    if not x_api_key or x_api_key != api_key:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    return {
        "report_generated": datetime.now().isoformat(),
        "summary": {
            "total_scams_detected": scam_statistics["scams_detected"],
            "unique_criminals_identified": len(scam_statistics["intelligence_collected"]["upi_ids"]) + 
                                          len(scam_statistics["intelligence_collected"]["emails"]) +
                                          len(scam_statistics["intelligence_collected"]["phone_numbers"])
        },
        "collected_intelligence": {
            "upi_ids": list(scam_statistics["intelligence_collected"]["upi_ids"]),
            "bank_accounts": list(scam_statistics["intelligence_collected"]["bank_accounts"]),
            "phishing_links": list(scam_statistics["intelligence_collected"]["phishing_links"]),
            "phone_numbers": list(scam_statistics["intelligence_collected"]["phone_numbers"]),
            "emails": list(scam_statistics["intelligence_collected"]["emails"])
        },
        "scam_breakdown": dict(scam_statistics["scam_types"]),
        "recommendations": [
            "Report UPI IDs to NPCI for blocking",
            "Report phishing links to domain registrars",
            "File FIR with cyber crime cell with this evidence",
            "Share phone numbers with telecom providers for blocking"
        ]
    }

@app.get("/")
async def root():
    return {
        "message": "Honeypot Scam Detection API is running",
        "version": "2.0",
        "features": [
            "Multi-turn conversation tracking",
            "Enhanced intelligence extraction (UPI, bank, phone, email, crypto)",
            "Real-time analytics dashboard",
            "Risk scoring system (0-100)",
            "Law enforcement reporting"
        ],
        "endpoints": {
            "analyze": "POST /honeypot/analyze",
            "conversation_history": "GET /conversation/{id}",
            "analytics": "GET /analytics",
            "intelligence_report": "GET /intelligence/report",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "total_conversations": len(conversation_history),
        "total_analyzed": scam_statistics["total_analyzed"],
        "scams_detected": scam_statistics["scams_detected"]
    }
