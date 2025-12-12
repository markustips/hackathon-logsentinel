#!/bin/bash

# Build script for backend deployment on Render
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating required directories..."
mkdir -p data/faiss_index data/uploads

echo "Backend build completed successfully!"