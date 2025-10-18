# Hemut Voice AI - Backend

🚚 **AI-powered driver status checking system** built with FastAPI and Vapi.ai

## ✅ **SYSTEM STATUS: FULLY FUNCTIONAL**

### 🎯 **Live Test Results (Oct 18, 2025)**
```
📞 Test Call #1: Driver said "No" 
   → AI Response: Asked for reason
   → Driver: "traffic and was busy in something"
   → Result: ✅ Database updated to "Available" with reason
   → Status: SUCCESS ✅

📞 Test Call #2: Driver said "Yes"
   → AI Response: Confirmed pickup
   → Result: ✅ Database updated to "Loaded"
   → Status: SUCCESS ✅
```

## 🚀 **Features (100% Working)**

- ✅ **Real AI Voice Calls** - Vapi.ai integration with GPT-4o
- ✅ **International Calling** - Twilio integration (+91 India numbers)
- ✅ **Dynamic Driver Lookup** - Phone number based identification
- ✅ **Real-time Database Updates** - Supabase PostgreSQL
- ✅ **Intelligent Webhooks** - Processes AI function calls
- ✅ **Call Logging** - Complete conversation history
- ✅ **Auto Status Updates** - Loaded/Available based on AI conversation
- ✅ **Error Handling** - Multiple phone format support
- ✅ **No Hardcoding** - 100% dynamic data flow

## 🛠 **Tech Stack**

- **Framework**: FastAPI (Python)
- **AI Voice**: Vapi.ai (GPT-4o + Elliot voice)
- **Telephony**: Twilio (International calling)
- **Database**: Supabase (PostgreSQL)
- **Webhooks**: Real-time AI response processing

## 📋 **API Endpoints**

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/api/drivers` | GET | Get all drivers | ✅ Working |
| `/api/call-logs` | GET | Get call history | ✅ Working |
| `/api/make-call` | POST | Initiate AI call | ✅ Working |
| `/api/vapi/webhook` | POST | Vapi webhook handler | ✅ Working |
| `/api/vapi/webhook` | GET | Webhook health check | ✅ Working |

## 🔧 **Setup**

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables** (create `.env`):
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   VAPI_API_KEY=your_vapi_private_key
   VAPI_PHONE_NUMBER=your_phone_number_id
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   ```

3. **Run the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## 🌐 **Deployment Options**

### **Recommended: Railway (Easiest)**
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Built-in environment variables
- ✅ PostgreSQL add-on available

### **AWS (Free Tier Available)**
- ✅ EC2 Free Tier (12 months)
- ✅ RDS Free Tier (12 months)
- ✅ Lambda (serverless option)
- ⚠️ Requires more setup

### **Other Options**
- Heroku (paid)
- Google Cloud Run
- DigitalOcean App Platform

## ⚠️ **Deployment Considerations**

1. **Environment Variables**: Secure storage required
2. **Webhook URL**: Must be HTTPS for Vapi
3. **Database**: Supabase handles this automatically
4. **Phone Numbers**: Twilio integration already configured
5. **CORS**: Already configured for frontend

## 🔍 **Vapi.ai Integration Details**

- ✅ **100% Vapi.ai Based** - No other AI services used
- ✅ **GPT-4o Model** - Latest OpenAI model via Vapi
- ✅ **Elliot Voice** - Professional voice synthesis
- ✅ **Function Calling** - AI calls `updateLoadStatus` function
- ✅ **Webhook Processing** - Real-time response handling
- ✅ **International Support** - Twilio integration for global calls

## 📊 **System Architecture**

```
Frontend (React) → Backend (FastAPI) → Vapi.ai → Twilio → Driver's Phone
                                    ↓
                              Webhook Response
                                    ↓
                            Supabase Database Update
                                    ↓
                            Frontend Auto-refresh
```

## 🎯 **Next Steps for Production**

1. Deploy backend to Railway/AWS
2. Update frontend API_URL to production URL
3. Deploy frontend to Vercel
4. Update Vapi webhook URL to production
5. Test end-to-end in production environment