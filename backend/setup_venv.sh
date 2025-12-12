#!/bin/bash

echo "Setting up Python virtual environment..."

# Activate virtual environment (Windows Git Bash compatible)
source venv/Scripts/activate || source venv/bin/activate

echo ""
echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing core packages..."
pip install fastapi uvicorn python-multipart sqlmodel pydantic python-dotenv

echo ""
echo "Installing LangChain packages..."
pip install langchain==1.1.2 langgraph==1.0.4 langchain-anthropic==1.2.0 langchain-google-genai==2.0.6

echo ""
echo "Installing ML packages..."
pip install sentence-transformers scikit-learn pandas faiss-cpu

echo ""
echo "Installation complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/Scripts/activate  (or venv/bin/activate on Linux/Mac)"
echo "  python start_server.py"
