FROM apache/spark:3.5.0

# Install Python dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /lakehouse

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p /var/lib/lakehouse/{bronze,silver,gold,staging,archive,logs}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Run API server
EXPOSE 8888
CMD ["python3", "api/lakehouse_api.py"]
