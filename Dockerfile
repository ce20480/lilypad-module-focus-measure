FROM python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libgl1 \
  libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install module dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src
COPY models ./models

# Set environment variables
ENV HF_HOME=/app/models \
TRANSFORMERS_OFFLINE=1 \ 
PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1

# Ensure we can write to our output directory
RUN mkdir -p /outputs && chmod 755 /outputs

# Set entrypoint
ENTRYPOINT ["python", "/app/src/run_inference.py"]
