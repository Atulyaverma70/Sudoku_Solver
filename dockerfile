# Python + slim base keeps image small
FROM python:3.11-slim

# System deps for Tesseract + OpenCV codecs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng \
    libgl1 libglib2.0-0 \
    libjpeg62-turbo zlib1g libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# App setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render provides $PORT; bind to it via gunicorn
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
EXPOSE 10000

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000", "--workers", "2", "--timeout", "120"]
