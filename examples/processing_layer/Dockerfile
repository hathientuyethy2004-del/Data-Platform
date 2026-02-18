# Processing Layer Dockerfile
# Runs Spark streaming and batch jobs

FROM python:3.11-slim

WORKDIR /processing

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and outputs
RUN mkdir -p /var/lib/spark/logs /var/lib/spark/outputs /var/lib/spark/checkpoints

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SPARK_MASTER=local[*]
ENV KAFKA_BOOTSTRAP_SERVER=kafka:9092
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Run orchestrator
CMD ["python", "orchestrator.py"]
