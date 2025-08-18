# Use slim Python and install system deps + Tesseract
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system packages: tesseract + libraries OpenCV needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Hint pytesseract where the binary is (your ocr_processing.py reads this)
ENV TESSERACT_CMD=/usr/bin/tesseract

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Render will inject $PORT; bind gunicorn to it
CMD ["bash", "-lc", "gunicorn -b 0.0.0.0:$PORT app:app"]
