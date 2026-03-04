# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for ChromaDB and other ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define environment variables
ENV PYTHONUNBUFFERED=1

# Overwrite sqlite3 with pysqlite3-binary for ChromaDB compatibility on Linux
ENV CHROMA_SQLITE_IMPL=sqlite3

# Run the application using gunicorn for production stability
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app", "--timeout", "120"]
