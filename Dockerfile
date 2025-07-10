FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY init_db.py .
COPY templates/ ./templates/
COPY data/ ./data/
COPY static/ ./static/

# Create necessary directories
RUN mkdir -p /app/data /app/static/images

# Set environment variables
ENV DATABASE_PATH=/app/data/pals.db
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create a startup script
COPY start.sh .
RUN dos2unix start.sh && chmod +x start.sh

# Expose port for Flask app
EXPOSE 5000

# Default command to run the startup script
CMD ["/app/start.sh"] 