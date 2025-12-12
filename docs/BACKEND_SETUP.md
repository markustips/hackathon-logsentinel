# LogSentinel AI Backend Setup Guide

## Quick Start

### 1. Setup Virtual Environment

We've created a Python virtual environment to isolate dependencies:

**On Windows (CMD):**
```cmd
cd backend
activate_and_install.bat
```

**On Windows (Git Bash) or Linux/Mac:**
```bash
cd backend
bash setup_venv.sh
```

### 2. Start the Server

**Using the helper script (recommended):**

Windows CMD:
```cmd
run_server.bat
```

Git Bash/Linux/Mac:
```bash
source venv/Scripts/activate  # Windows Git Bash
# OR
source venv/bin/activate      # Linux/Mac

python start_server.py
```

**Manual start (if you need more control):**
```bash
# Activate venv first
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# Then start with uvicorn
uvicorn main:app --reload --port 8000
```

The server will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## What We Fixed

### 1. LangChain Debug AttributeError ✅

**Problem:** `AttributeError: module 'langchain' has no attribute 'debug'`

**Solution:** Created `start_server.py` that patches the langchain module before starting uvicorn:

```python
import langchain
langchain.debug = False
langchain.verbose = False
```

**Why it happened:** Newer versions of `langchain-core` expect the `langchain` module to have `debug` and `verbose` attributes, but they're not present in langchain 1.1.2.

### 2. Module Import Errors ✅

**Problem:** `ModuleNotFoundError: No module named 'backend'`

**Solution:** Changed all imports from absolute (`from backend.X`) to relative (`from X`) throughout the codebase.

**Files modified:**
- `main.py`
- `database.py`
- All files in `routers/`
- All files in `agents/`

### 3. SQLAlchemy Reserved Name Error ✅

**Problem:** `Attribute name 'metadata' is reserved`

**Solution:** Renamed `LogRecord.metadata` field to `LogRecord.extra_data` throughout:
- `models.py`
- `services/parser.py`
- `routers/upload.py`

### 4. Gemini API Integration ✅

**Status:** Working perfectly with `gemini-2.5-flash-lite` model

**Configuration:**
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSyDDdXaMgLiq4GpfxlKZhUpw4ssKN3-Nyto
GEMINI_MODEL=gemini-2.5-flash-lite
```

---

## Virtual Environment

### Why Use a Virtual Environment?

1. **Dependency Isolation:** Keeps project dependencies separate from system Python
2. **Version Control:** Ensures consistent package versions across team members
3. **Cleaner System:** Doesn't pollute global Python installation
4. **Easier Deployment:** Simpler to replicate environment on production servers

### Virt Envual Environment Structure

```
backend/
├── venv/                    # Virtual environment (not committed to git)
│   ├── Scripts/            # Windows activation scripts
│   ├── bin/                # Linux/Mac activation scripts
│   └── Lib/                # Installed packages
├── .env                    # Environment variables (contains API keys)
├── start_server.py         # Server startup with langchain patch
├── setup_venv.sh          # Setup script for Unix/Git Bash
├── activate_and_install.bat # Setup script for Windows CMD
└── run_server.bat          # Run script for Windows CMD
```

### Manual Virtual Environment Commands

**Create venv:**
```bash
python -m venv venv
```

**Activate venv:**
```bash
# Windows CMD
venv\Scripts\activate.bat

# Windows PowerShell
venv\Scripts\Activate.ps1

# Git Bash (Windows)
source venv/Scripts/activate

# Linux/Mac
source venv/bin/activate
```

**Deactivate venv:**
```bash
deactivate
```

**Check if venv is active:**
```bash
which python  # Should show venv/Scripts/python or venv/bin/python
```

---

## Installed Packages

### Core Web Framework
- `fastapi==0.116.1` - Modern web framework
- `uvicorn==0.35.0` - ASGI server
- `python-multipart==0.0.20` - File upload support
- `sqlmodel==0.0.27` - SQL ORM
- `pydantic==2.12.3` - Data validation
- `python-dotenv==1.1.1` - Environment variable management

### LangChain & AI
- `langchain==1.1.2` - LLM framework
- `langgraph==1.0.4` - Multi-agent workflows
- `langchain-anthropic==1.2.0` - Anthropic Claude integration
- `langchain-google-genai==2.0.6` - Google Gemini integration
- `langchain-core==1.1.1` - Core abstractions

### ML & Data Processing
- `sentence-transformers>=2.2.0` - Text embeddings
- `scikit-learn>=1.4.0` - ML algorithms (Isolation Forest)
- `pandas>=2.1.0` - Data manipulation
- `faiss-cpu>=1.7.4` - Vector similarity search

---

## Testing

### Test Gemini Connection

```bash
python test_simple.py
```

Expected output:
```
Testing Gemini API...
Testing with gemini-2.5-flash-lite...
[OK] LLM instance created
[OK] Sending test query...

[SUCCESS] Gemini responded: OK

Gemini API is working!
```

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","service":"LogSentinel AI"}`

### View API Documentation

Visit http://localhost:8000/docs in your browser

---

## Troubleshooting

### Error: "Module langchain has no attribute debug"
**Solution:** Always use `python start_server.py` instead of `uvicorn main:app` directly

### Error: "ModuleNotFoundError: No module named 'X'"
**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/Scripts/activate  # Activate first
pip install -r ../requirements.txt
```

### Error: "Cannot find .env file"
**Solution:** Copy `.env.example` to `.env` and add your API keys:
```bash
cp ../.env.example .env
```

### Gemini API Quota Exceeded
**Solution:**
1. Wait for quota to reset (usually per minute)
2. Check usage at: https://ai.dev/usage
3. Try a different model (e.g., `gemini-1.5-flash`)
4. Use a different API key

### Windows: Scripts not executing
**Solution:** On Windows, you might need to allow script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Development Workflow

1. **Activate venv:**
   ```bash
   source venv/Scripts/activate
   ```

2. **Make code changes**

3. **Test changes:**
   ```bash
   python start_server.py
   ```

4. **Server auto-reloads on file changes** (thanks to `--reload` flag)

5. **Deactivate when done:**
   ```bash
   deactivate
   ```

---

## Production Deployment

For production, you should:

1. Use PostgreSQL instead of SQLite
2. Set `LOG_LEVEL=WARNING`
3. Remove `--reload` flag from uvicorn
4. Use a production ASGI server (e.g., gunicorn + uvicorn workers)
5. Set up proper authentication
6. Use HTTPS
7. Set up monitoring and logging

Example production command:
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Next Steps

1. ✅ Virtual environment set up
2. ✅ Dependencies installed
3. ✅ Gemini integration working
4. ✅ LangChain patch applied
5. 🎯 **Ready to start the server and test the multi-agent copilot!**

Run: `python start_server.py`

Then upload a log file via the frontend or API to test the full system.
