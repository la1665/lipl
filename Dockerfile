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
# COPY .cert .
# EXPOSE 8000

# CMD ["uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD ["uvicorn", "main:app_socket", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/cert/client.key", "--ssl-certfile", "/app/cert/client.crt", "--ssl-ca-certs", "/app/cert/ca.crt"]
