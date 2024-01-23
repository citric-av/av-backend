# Stage 1: Base image with dependencies
FROM python:3.9.18-bullseye as base

WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Setup for Flask app
FROM base as flask-app
COPY . .
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]

# Stage 3: Setup for Worker
FROM base as worker
COPY . .
CMD ["python", "worker.py"]
