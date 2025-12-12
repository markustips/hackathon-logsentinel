"""
Start script for LogSentinel AI backend.
This script applies necessary patches before starting uvicorn.
"""
import os
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Fix for langchain.debug AttributeError - MUST be set before any imports
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# Patch langchain module
import langchain

# Patch all missing attributes that langchain-core expects
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = None

print("[OK] Applied langchain patches (debug, verbose, llm_cache)")
print("[OK] Disabled LangChain tracing")

# Now start uvicorn
import uvicorn

if __name__ == "__main__":
    print("\nStarting LogSentinel AI Backend...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("API docs available at: http://127.0.0.1:8000/docs")
    print("\nPress CTRL+C to stop\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
