FROM python:3.11-slim

# System deps for OpenCV and Tesseract
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tesseract-ocr \
      libgl1 \
      libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# App
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Env
ENV PYTHONUNBUFFERED=1
# Render provides $PORT; gunicorn will bind to it
CMD exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 app:app
