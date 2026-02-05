# Deployment Guide - GUVI Honeypot API

## ⚠️ Pre-Deployment Checklist

### 1. Security Check
- [ ] Remove all real API keys from code
- [ ] Remove API keys from README files
- [ ] Remove API keys from comments
- [ ] Add `.env` to `.gitignore`
- [ ] Never commit `.env` file to git

### 2. Environment Variables
Set these on your deployment platform:

```
API_KEY=<generate-strong-random-key>
XAI_API_KEY=<your-xai-key-from-console.x.ai>
XAI_MODEL=grok-3
```

### 3. Test GUVI Callback
Before deploying, verify callback works:
- Run test with scam message
- Check server logs for "GUVI CALLBACK RESPONSE"
- Verify status code is 200 or 201
- Confirm payload was sent correctly

---

## Recommended Deployment Platforms

### Option 1: Render (Recommended)

**Pros:**
- Free tier available
- Easy deployment from GitHub
- Automatic HTTPS
- Good uptime

**Steps:**

1. **Push to GitHub** (without .env file!)
```bash
git init
git add .
git commit -m "GUVI Honeypot API"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Deploy on Render**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     - **Name:** guvi-honeypot-api
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn main_guvi:app --host 0.0.0.0 --port $PORT`
     - **Instance Type:** Free (or Starter for "Always On")

3. **Set Environment Variables**
   - In Render dashboard, go to "Environment"
   - Add:
     - `API_KEY` = your-secret-key
     - `XAI_API_KEY` = your-xai-key
     - `XAI_MODEL` = grok-3

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)
   - Get your public URL: `https://guvi-honeypot-api.onrender.com`

**Important for Render Free Tier:**
- Service sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- For evaluation, consider upgrading to Starter ($7/month) for "Always On"

---

### Option 2: Railway

**Pros:**
- $5 free credit
- No sleep issues
- Fast deployment

**Steps:**

1. **Deploy on Railway**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo

2. **Configure**
   - Railway auto-detects Python
   - Set environment variables in dashboard
   - Start command: `uvicorn main_guvi:app --host 0.0.0.0 --port $PORT`

3. **Get URL**
   - Railway provides: `https://your-app.up.railway.app`

---

### Option 3: Fly.io

**Pros:**
- Free tier with 3 VMs
- No sleep issues
- Global deployment

**Steps:**

1. **Install Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login and Launch**
```bash
fly auth login
fly launch
```

3. **Set Secrets**
```bash
fly secrets set API_KEY=your-secret-key
fly secrets set XAI_API_KEY=your-xai-key
fly secrets set XAI_MODEL=grok-3
```

4. **Deploy**
```bash
fly deploy
```

---

## Post-Deployment Verification

### 1. Test Health Check
```bash
curl https://your-deployed-url.com/health
```

Expected: `{"status":"healthy"}`

### 2. Test Scam Detection
```bash
curl -X POST https://your-deployed-url.com/honeypot/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "deploy_test_001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Pay to scammer@paytm",
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

Expected: `{"status":"success","reply":"..."}`

### 3. Verify GUVI Callback in Logs

Check your deployment platform logs for:
```
🔔 SENDING GUVI CALLBACK for session: deploy_test_001
✅ GUVI CALLBACK RESPONSE:
   Status Code: 200
   Response Text: ...
```

**If callback fails:**
- Check if GUVI endpoint is accessible
- Verify payload format matches GUVI requirements
- Check timeout settings (currently 5 seconds)

---

## Monitoring During Evaluation

### Check These Regularly:

1. **Server Uptime**
   - Render: Check dashboard for "Running" status
   - Railway: Monitor in dashboard
   - Fly.io: `fly status`

2. **Logs**
   - Render: View logs in dashboard
   - Railway: Real-time logs in dashboard
   - Fly.io: `fly logs`

3. **GUVI Callback Success Rate**
   - Look for "✅ GUVI callback SUCCESS" in logs
   - If seeing errors, investigate immediately

---

## Troubleshooting

### Issue: Service Sleeping (Render Free Tier)
**Solution:** 
- Upgrade to Starter plan ($7/month) for "Always On"
- Or use Railway/Fly.io which don't sleep

### Issue: GUVI Callback Timeout
**Solution:**
- Increase timeout from 5 to 10 seconds
- Check network connectivity from deployment platform

### Issue: 500 Internal Server Error
**Solution:**
- Check logs for Python errors
- Verify all dependencies in requirements.txt
- Ensure environment variables are set

### Issue: 401 Unauthorized
**Solution:**
- Verify API_KEY is set in environment variables
- Check if client is sending correct x-api-key header

---

## Requirements.txt

Ensure your `requirements.txt` includes:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
pydantic==2.5.3
openai==1.54.0
python-dotenv==1.0.0
```

---

## .gitignore

Create `.gitignore` file:
```
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
*.log
.DS_Store
```

---

## Final Checklist Before Submission

- [ ] API deployed and accessible via HTTPS
- [ ] Health check returns 200
- [ ] Test scam detection works
- [ ] GUVI callback logs show success (200/201)
- [ ] No real API keys in public code/docs
- [ ] Service won't sleep during evaluation
- [ ] Logs are accessible for debugging
- [ ] Public URL documented for GUVI team

---

## Submit to GUVI

Provide them with:
1. **Public API URL:** `https://your-app.onrender.com`
2. **API Key:** (the one you set in environment)
3. **Test Endpoint:** `POST /honeypot/analyze`
4. **Health Check:** `GET /health`

---

## Emergency Contacts

If deployment fails during evaluation:
1. Check platform status pages
2. Have backup deployment ready
3. Monitor logs continuously
4. Keep deployment dashboard open

Good luck! 🚀
