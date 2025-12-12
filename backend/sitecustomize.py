"""
sitecustomize.py - Automatically imported by Python before any other modules.
This file patches the langchain module to fix the AttributeError: module 'langchain' has no attribute 'debug'
"""
import os

# Disable LangChain tracing
os.environ.setdefault("LANGCHAIN_TRACING", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

# Patch langchain module
try:
    import langchain

    if not hasattr(langchain, 'debug'):
        langchain.debug = False

    if not hasattr(langchain, 'verbose'):
        langchain.verbose = False

    if not hasattr(langchain, 'llm_cache'):
        langchain.llm_cache = None

except ImportError:
    # langchain not installed yet, will be patched when it is imported
    pass
