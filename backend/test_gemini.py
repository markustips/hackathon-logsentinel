"""Test Gemini integration."""
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Gemini integration...")

try:
    from config import get_settings
    settings = get_settings()

    print(f"[OK] LLM Provider: {settings.llm_provider}")
    print(f"[OK] Gemini Model: {settings.gemini_model}")
    print(f"[OK] Google API Key: {settings.google_api_key[:20]}...")

    print("\n[OK] Importing LLM service...")
    from services.llm import get_llm

    print("[OK] Creating LLM instance...")
    llm = get_llm(temperature=0)

    print("[OK] Testing simple query...")
    from langchain_core.messages import HumanMessage

    response = llm.invoke([HumanMessage(content="Say 'Hello from Gemini!' and nothing else.")])

    print(f"\n[SUCCESS] Gemini responded: {response.content}\n")
    print("gemini-2.5-flash-lite is working perfectly!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
