FROM nvidia/cuda:11.8.0-devel-ubuntu20.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directories
RUN mkdir -p /tmp/.transformers /tmp/.torch

# Set environment variables
ENV TRANSFORMERS_CACHE=/tmp/.transformers
ENV TORCH_HOME=/tmp/.torch
ENV CUDA_VISIBLE_DEVICES=0

# Expose port
EXPOSE 8000

# Health check with longer timeout for GPU models
HEALTHCHECK --interval=30s --timeout=60s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "app.py"]
