FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . .

# Expose ports
# 5353/udp for DNS (mapped to host 53/udp in production to run without root inside container)
# 8080/tcp for Flask Web Dashboard
EXPOSE 5353/udp
EXPOSE 8080/tcp

# Default command runs the DNS blocker
CMD ["python", "dns_blocker.py"]
