FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/faiss_index /app/data/uploads

# Expose port (Render will set PORT environment variable)
EXPOSE $PORT

# Run the application with dynamic port
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
