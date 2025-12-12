#!/bin/bash

# Start script for backend deployment on Render
echo "Starting LogSentinel AI Backend..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}