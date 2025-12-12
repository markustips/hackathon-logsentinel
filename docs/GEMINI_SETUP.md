# Using Google Gemini with LogSentinel AI

LogSentinel AI now supports **Google Gemini** as an alternative to Anthropic Claude! This gives you flexibility in choosing your LLM provider.

## 🚀 Quick Setup

### Step 1: Get a Google AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

**Note**: Gemini API is free for testing with generous quotas!

### Step 2: Install Required Packages

```bash
# Install Gemini support
pip install langchain-google-genai google-generativeai
```

### Step 3: Configure Environment

Edit your `.env` file:

```bash
# Set LLM provider to Gemini
LLM_PROVIDER=gemini

# Add your Google API key
GOOGLE_API_KEY=your_google_api_key_here

# Choose Gemini model (flash is faster, pro is more powerful)
GEMINI_MODEL=gemini-1.5-flash
```

### Step 4: Run the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

That's it! The system will now use Google Gemini instead of Claude.

---

## 📊 Gemini Models Comparison

### gemini-1.5-flash (Default)
- **Speed**: Very fast ⚡
- **Cost**: Free tier available
- **Best for**: Development, demos, real-time applications
- **Context**: 1M tokens
- **Rate limit**: 15 RPM (free tier)

### gemini-1.5-pro
- **Speed**: Moderate
- **Cost**: Pay per use (affordable)
- **Best for**: Production, complex analysis
- **Context**: 2M tokens
- **Rate limit**: 2 RPM (free tier)

---

## 🔄 Switching Between Providers

### Use Gemini (Default)
```bash
# .env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
```

### Use Claude
```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Just change `LLM_PROVIDER` and restart the backend!

---

## ⚡ Performance Comparison

| Feature | Gemini 1.5 Flash | Claude 3.5 Sonnet |
|---------|------------------|-------------------|
| **Speed** | ⚡⚡⚡ Very Fast | ⚡⚡ Fast |
| **Cost** | 💰 Free tier | 💰💰 Paid |
| **Context** | 1M tokens | 200k tokens |
| **Quality** | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Outstanding |
| **Rate Limit** | 15 RPM (free) | Varies |
| **Best For** | Demos, dev | Production |

---

## 💡 Recommendations

### For Hackathons & Demos
**Use Gemini 1.5 Flash:**
- ✅ Free tier
- ✅ Very fast responses
- ✅ Great quality
- ✅ High context window

```bash
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
```

### For Production
**Use Gemini 1.5 Pro or Claude:**
- Gemini Pro: Good balance of cost and quality
- Claude Sonnet: Best quality for complex analysis

---

## 🛠️ Troubleshooting

### Error: "GOOGLE_API_KEY not set"

**Solution:**
```bash
# Check your .env file
cat .env | grep GOOGLE_API_KEY

# Make sure it's set
GOOGLE_API_KEY=your_actual_key_here
```

### Error: "Rate limit exceeded"

**Solution 1**: Use Flash model (higher rate limits)
```bash
GEMINI_MODEL=gemini-1.5-flash
```

**Solution 2**: Add delays between requests
```python
# The system handles this automatically
```

**Solution 3**: Upgrade to paid tier
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Enable billing for higher quotas

### Error: "convert_system_message_to_human"

This is normal! Gemini doesn't support system messages natively, so we automatically convert them. The system handles this transparently.

---

## 📋 Example .env File

```bash
# LogSentinel AI Configuration

# LLM Provider
LLM_PROVIDER=gemini

# Google Gemini API Key
GOOGLE_API_KEY=AIzaSyC-your-actual-key-here

# Gemini Model
GEMINI_MODEL=gemini-1.5-flash

# Database
DATABASE_URL=sqlite:///./logsentinel.db

# FAISS Index
FAISS_INDEX_PATH=./data/faiss_index

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Logging
LOG_LEVEL=INFO
```

---

## 🔍 Verifying Configuration

Test your setup:

```bash
cd backend
python -c "from services.llm import get_llm; llm = get_llm(); print('✅ LLM configured successfully!')"
```

Expected output:
```
INFO:     Using Google Gemini (gemini-1.5-flash)
✅ LLM configured successfully!
```

---

## 💰 Cost Comparison

### Free Tier Limits

**Google Gemini (Free):**
- Flash: 15 requests/minute, 1M requests/day
- Pro: 2 requests/minute, 50 requests/day
- Cost: $0

**Anthropic Claude:**
- No free tier
- Pay per use from day 1
- ~$3-$15 per million tokens

**For a hackathon demo, Gemini is perfect!** 🎉

---

## 🎯 Best Practices

### 1. Use Flash for Development
```bash
GEMINI_MODEL=gemini-1.5-flash
```

### 2. Rate Limiting
The system handles rate limits automatically. No code changes needed!

### 3. Error Handling
Both providers work with the same interface:
```python
from services.llm import get_llm

llm = get_llm()  # Automatically uses configured provider
response = llm.invoke(messages)
```

### 4. Monitoring Usage
Check your usage at:
- Gemini: https://makersuite.google.com/app/apikey
- Claude: https://console.anthropic.com/

---

## 📚 Additional Resources

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Pricing](https://ai.google.dev/pricing)
- [LangChain Gemini Integration](https://python.langchain.com/docs/integrations/chat/google_generative_ai)

---

## ✅ Quick Checklist

- [ ] Get Google AI API key
- [ ] Install packages: `pip install langchain-google-genai google-generativeai`
- [ ] Set `LLM_PROVIDER=gemini` in `.env`
- [ ] Set `GOOGLE_API_KEY=your_key` in `.env`
- [ ] Choose model: `GEMINI_MODEL=gemini-1.5-flash`
- [ ] Restart backend
- [ ] Test with a query!

---

**You're all set!** LogSentinel AI will now use Google Gemini for all AI operations. 🚀

**For hackathons**: Gemini 1.5 Flash is perfect - fast, free, and powerful!
