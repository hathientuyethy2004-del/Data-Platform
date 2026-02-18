FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Expose port used by uvicorn
EXPOSE 8000

CMD ["/bin/bash", "-lc", "python -c \"from platform.bootstrap import start_platform_services; start_platform_services(); from serving_layer.server import get_serving_layer; get_serving_layer().start()\""]
