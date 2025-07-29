FROM python:3.9-slim

# Install FFmpeg without sudo
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "scripts/api_server.py"]
