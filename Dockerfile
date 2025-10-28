# Dockerfile
# Use a lightweight, official Python image
FROM python:3.11-slim

# Set the working directory for the application code
WORKDIR /app

# Copy requirements and install dependencies (optimizes for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Set a default command (can be overridden by docker-compose)
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_config.py"]