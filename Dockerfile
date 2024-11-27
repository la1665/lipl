FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    curl

# Clean up the apt cache to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Create the logs directory with appropriate permissions
RUN mkdir -p logs && chmod 755 logs
# COPY .cert .
# EXPOSE 8000

# CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app_socket"]
#CMD ["gunicorn", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app_socket"]
CMD ["uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
# CMD ["uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/cert/client.key", "--ssl-certfile", "/app/cert/client.crt", "--ssl-ca-certs", "/app/cert/ca.crt"]
