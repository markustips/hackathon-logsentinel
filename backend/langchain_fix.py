"""
Fix for langchain.debug AttributeError.

This module patches the langchain module to add the 'debug' and 'verbose' attributes
that langchain-core expects but are missing in newer versions.

Import this module BEFORE any other langchain imports.
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

except ImportError:
    # langchain not installed yet
    pass
