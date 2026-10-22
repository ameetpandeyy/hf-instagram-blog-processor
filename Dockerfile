FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (updated for Debian Trixie)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models at build time (speeds up startup)
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli', device=-1)" || echo "Model download failed, will retry at runtime"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models/cached fonts logs

# Expose port for HuggingFace Spaces
EXPOSE 7860

# Set environment variable for HF Space
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
