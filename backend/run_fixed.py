#!/usr/bin/env python
"""
Fixed server runner that patches langchain.debug before any imports.
Use this instead of running uvicorn directly.
"""
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# CRITICAL: Set environment variables FIRST
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# CRITICAL: Patch langchain module BEFORE any other imports
import langchain

# Patch all missing attributes that langchain-core expects
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = None

print("[OK] Patched langchain.debug = False")
print("[OK] Patched langchain.verbose = False")
print("[OK] Patched langchain.llm_cache = None")
print("[OK] Disabled LangChain tracing\n")

# Now it's safe to import and run the app
if __name__ == "__main__":
    import uvicorn

    print("Starting LogSentinel AI Backend...")
    print("Server: http://127.0.0.1:8000")
    print("Docs: http://127.0.0.1:8000/docs")
    print("\nPress CTRL+C to stop\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
