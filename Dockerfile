# Multi-stage Dockerfile for UZEX AI Analyst
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code and database
COPY backend/ ./backend/
COPY db/ ./db/
COPY frontend/dist/ ./frontend/dist/
COPY run_server.py .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "run_server.py"]
