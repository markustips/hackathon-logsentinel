#!/bin/bash

# Start script for backend deployment on Render
echo "Starting LogSentinel AI Backend..."
echo "PORT: ${PORT}"
echo "DATABASE_URL: ${DATABASE_URL}"

# Run database migrations/setup
python -c "from database import create_db_and_tables; create_db_and_tables()"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}