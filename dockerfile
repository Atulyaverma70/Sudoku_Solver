# Use slim python base
FROM python:3.10-slim

# Install system dependencies (tesseract + OpenCV deps)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirement files first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Render injects $PORT)
EXPOSE 10000

# Use gunicorn in production
CMD gunicorn app:app --bind 0.0.0.0:$PORT
