#!/bin/bash

# Start script for backend deployment on Render
echo "Starting LogSentinel AI Backend..."
echo "PORT: ${PORT}"
echo "DATABASE_URL: ${DATABASE_URL}"

# Create required directories
echo "Creating data directories..."
mkdir -p /app/data/faiss_index /app/data/uploads
chmod 755 /app/data /app/data/faiss_index /app/data/uploads

# Verify directories exist
if [ -d "/app/data/uploads" ]; then
    echo "✓ Upload directory created: /app/data/uploads"
else
    echo "✗ Failed to create upload directory"
fi

if [ -d "/app/data/faiss_index" ]; then
    echo "✓ FAISS index directory created: /app/data/faiss_index"
else
    echo "✗ Failed to create FAISS index directory"
fi

# Run database migrations/setup
echo "Initializing database..."
python -c "from database import create_db_and_tables; create_db_and_tables()"

# Start the application
echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}