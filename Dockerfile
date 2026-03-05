# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir flask werkzeug

# Expose the port Flask runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
