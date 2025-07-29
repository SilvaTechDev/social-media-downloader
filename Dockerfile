FROM python:3.9-slim

# Install system dependencies (FFmpeg + cleanup)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create persistent download directory
RUN mkdir -p /tmp/downloads

CMD ["python", "scripts/api_server.py"]
