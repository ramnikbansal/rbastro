# Use a stable Python 3.10 slim image (good compatibility for swisseph)
FROM python:3.11-slim

# Avoid prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages required to compile/link swisseph and common Python deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first (Docker cache optimization)
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python deps
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Expose port (conventional port)
EXPOSE 5000

# Start command: bind to PORT env if provided, otherwise 5000.
# Uses gunicorn to serve the Flask app (app.py must define app = Flask(__name__))
CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT:-5000}"]
