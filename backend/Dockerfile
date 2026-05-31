# Use the official slim Python image (smaller download, faster builds)
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed by psycopg2 (PostgreSQL driver)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first so Docker can cache the pip install layer.
# If only source code changes, dependencies won't be reinstalled.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Uncomment to run as a non-root user (recommended for production)
# RUN useradd -m myuser
# USER myuser

EXPOSE 5000

# Run with Gunicorn instead of the Flask dev server; 3 worker processes
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]

