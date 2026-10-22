#!/bin/bash
# Quick start script for local development

echo "?? Instagram Blog Processor - Quick Start"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "?? Creating .env file from template..."
    cp .env.example .env
    echo "??  Please edit .env and add your API keys"
    exit 1
fi

echo "?? Installing dependencies..."
pip install -r requirements.txt

echo "???  Building Docker image..."
docker build -t instagram-blog-processor .

echo "? Setup complete!"
echo ""
echo "To run locally:"
echo "  make run           # Run with uvicorn"
echo "  make docker-run    # Run with Docker"
echo ""
echo "To test:"
echo "  make test          # Run tests"
echo "  curl http://localhost:7860/health"
