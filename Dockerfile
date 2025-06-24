FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY render_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r render_requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p flask_session

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main_render.py
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main_render:app"]