FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including snappy compression support
RUN apt-get update && apt-get install -y \
    gcc \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir kafka-python

# Copy simulator script
COPY simulator.py .

# Run simulator
CMD ["python", "simulator.py"]
