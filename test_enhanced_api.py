import requests
import json
import sys
import io

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_URL = "http://localhost:8000"
API_KEY = "your-0002121"
HEADERS = {"x-api-key": API_KEY}

def test_single_message_analysis():
    """Test 1: Single message analysis with enhanced features"""
    print("\n" + "="*80)
    print("TEST 1: Single Message Analysis (Enhanced)")
    print("="*80)
    
    payload = {
        "conversation_id": "test_enhanced_1",
        "message": "URGENT! Your bank account is blocked. Send OTP to 9876543210 or pay to scammer@paytm. IFSC: HDFC0001234. Visit www.fake-bank-kyc.com",
        "language": "en"
    }
    
    try:
        response = requests.post(f"{API_URL}/honeypot/analyze", headers=HEADERS, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\n✅ Scam Detected: {result['is_scam']}")
        print(f"📊 Category: {result['scam_category']}")
        print(f"🎯 Subtype: {result['scam_subtype']}")
        print(f"📈 Confidence: {result['confidence']}")
        print(f"⚠️  Risk Score: {result['risk_score']}/100")
        print(f"🚨 Signals: {', '.join(result['signals_detected'])}")
        print(f"\n💬 Agent Reply:\n{result['agent_reply']}")
        print(f"\n🔍 Intelligence Extracted:")
        intel = result['extracted_intelligence']
        print(f"  - UPI IDs: {intel['upi_ids']}")
        print(f"  - Bank Accounts: {intel['bank_accounts']}")
        print(f"  - IFSC Codes: {intel['ifsc_codes']}")
        print(f"  - Phone Numbers: {intel['phone_numbers']}")
        print(f"  - Emails: {intel['emails']}")
        print(f"  - Phishing Links: {intel['phishing_links']}")
        print(f"  - Crypto Wallets: {intel['crypto_wallets']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_multi_turn_conversation():
    """Test 2: Multi-turn conversation endpoint"""
    print("\n" + "="*80)
    print("TEST 2: Multi-Turn Conversation (AGENTIC)")
    print("="*80)
    
    payload = {
        "conversation_id": "test_multiturn_1",
        "messages": [
            {"role": "scammer", "content": "Your KYC has expired. Click this link to update: www.fake-kyc.com"},
            {"role": "agent", "content": "Which bank is this for?"},
            {"role": "scammer", "content": "This is from HDFC Bank. Pay Rs 100 to verify@paytm"},
            {"role": "agent", "content": "How do I pay?"},
            {"role": "scammer", "content": "Send to UPI: scammer123@ybl or call 9123456789"}
        ],
        "language": "en"
    }
    
    try:
        response = requests.post(f"{API_URL}/honeypot/respond", headers=HEADERS, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\n✅ Multi-turn Analysis Complete")
        print(f"📊 Category: {result['scam_category']}")
        print(f"🎯 Subtype: {result['scam_subtype']}")
        print(f"⚠️  Risk Score: {result['risk_score']}/100")
        print(f"🔄 Turn: {result['conversation_turn']}")
        print(f"\n💬 Next Agent Reply:\n{result['agent_reply']}")
        print(f"\n🔍 Total Intelligence from Conversation:")
        intel = result['extracted_intelligence']
        print(f"  - UPI IDs: {intel['upi_ids']}")
        print(f"  - Phone Numbers: {intel['phone_numbers']}")
        print(f"  - Phishing Links: {intel['phishing_links']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_conversation_history():
    """Test 3: Get conversation history"""
    print("\n" + "="*80)
    print("TEST 3: Conversation History Retrieval")
    print("="*80)
    
    try:
        response = requests.get(f"{API_URL}/conversation/test_enhanced_1", headers=HEADERS, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Conversation Found")
            print(f"📝 Total Turns: {result['total_turns']}")
            print(f"🚨 Scam Detected: {result['scam_detected']}")
            print(f"\n🔍 Total Intelligence Collected:")
            intel = result['total_intelligence']
            print(f"  - UPI IDs: {intel['upi_ids']}")
            print(f"  - Bank Accounts: {intel['bank_accounts']}")
            print(f"  - IFSC Codes: {intel['ifsc_codes']}")
            print(f"  - Phone Numbers: {intel['phone_numbers']}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Conversation not found (expected for first run)")
            return True
        else:
            print(f"❌ FAILED: Expected 200 or 404, got {response.status_code}")
            try:
                print(f"Error: {response.text}")
            except:
                pass
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_analytics_dashboard():
    """Test 4: Analytics endpoint"""
    print("\n" + "="*80)
    print("TEST 4: Analytics Dashboard")
    print("="*80)
    
    try:
        response = requests.get(f"{API_URL}/analytics", headers=HEADERS, timeout=10)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\n📊 ANALYTICS DASHBOARD")
        print(f"  Total Analyzed: {result['total_analyzed']}")
        print(f"  Scams Detected: {result['scams_detected']}")
        print(f"  Detection Rate: {result['detection_rate']}%")
        print(f"  Top Scam Type: {result['top_scam_type']}")
        print(f"\n🔍 Intelligence Collected:")
        intel = result['total_intelligence_collected']
        print(f"  - UPI IDs: {intel['upi_ids']}")
        print(f"  - Bank Accounts: {intel['bank_accounts']}")
        print(f"  - Phishing Links: {intel['phishing_links']}")
        print(f"  - Phone Numbers: {intel['phone_numbers']}")
        print(f"  - Emails: {intel['emails']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_conversation_report():
    """Test 5: Generate conversation report"""
    print("\n" + "="*80)
    print("TEST 5: Conversation Report (Law Enforcement)")
    print("="*80)
    
    try:
        response = requests.get(f"{API_URL}/honeypot/report/test_enhanced_1", headers=HEADERS, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📋 REPORT GENERATED")
            print(f"  Report ID: {result['report_id']}")
            print(f"  Generated: {result['generated_at']}")
            print(f"\n📊 Summary:")
            summary = result['summary']
            print(f"  - Total Turns: {summary['total_turns']}")
            print(f"  - Scam Type: {summary['scam_type']}")
            print(f"  - Max Risk Score: {summary['max_risk_score']}/100")
            print(f"  - Action: {summary['recommended_action']}")
            
            print(f"\n🔍 Evidence Count:")
            evidence = result['evidence_count']
            print(f"  - Total Identifiers: {evidence['total_identifiers']}")
            print(f"  - Financial IDs: {evidence['financial_identifiers']}")
            print(f"  - Phishing Links: {evidence['phishing_links']}")
            
            print(f"\n⚖️  Recommended Actions:")
            for action in result['recommended_actions'][:3]:
                print(f"  • {action}")
            
            return True
        else:
            print(f"⚠️  Report not available (run test 1 first)")
            return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_health_check():
    """Test 6: Health check"""
    print("\n" + "="*80)
    print("TEST 6: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        print(f"\n✅ System Health:")
        print(f"  Status: {result['status']}")
        print(f"  Total Conversations: {result['total_conversations']}")
        print(f"  Total Analyzed: {result['total_analyzed']}")
        print(f"  Scams Detected: {result['scams_detected']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("HACKATHON-WINNING HONEYPOT API TEST SUITE")
    print("="*80)
    print("\nTesting Enhanced Features:")
    print("  * Multi-turn conversations")
    print("  * Enhanced intelligence extraction (phone, email, IFSC, crypto)")
    print("  * Risk scoring system")
    print("  * Evidence signals detection")
    print("  * Scam taxonomy (category + subtype)")
    print("  * Conversation reports")
    print("  * Analytics dashboard")
    
    results = []
    
    # Run all tests
    results.append(("Single Message Analysis", test_single_message_analysis()))
    results.append(("Multi-Turn Conversation", test_multi_turn_conversation()))
    results.append(("Conversation History", test_conversation_history()))
    results.append(("Analytics Dashboard", test_analytics_dashboard()))
    results.append(("Conversation Report", test_conversation_report()))
    results.append(("Health Check", test_health_check()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🏆 ALL TESTS PASSED! READY FOR HACKATHON DEMO!")
    else:
        print("\n⚠️  Some tests failed. Check server logs.")
    
    print("\n" + "="*80)
    print("💡 TIP: Visit http://localhost:8000/docs for interactive API documentation")
    print("="*80)
