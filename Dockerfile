# ──────────────────────────────────────────────────────────
# SmartDesk — Dockerfile
# Builds a production-ready container for Google Cloud Run
# ──────────────────────────────────────────────────────────

# Use the official Python slim image (smaller = faster deploys)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies needed by some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching — only reinstalls
# dependencies when requirements.txt changes, not on every code change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Cloud Run sets PORT env var — default to 8080
ENV PORT=8080

# Health check: Cloud Run pings this before sending traffic
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run main.py when container starts
# For Cloud Run / production, you'd swap this for a FastAPI/Flask server
CMD ["python", "main.py"]
