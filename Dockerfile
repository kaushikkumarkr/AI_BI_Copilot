# file: Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Script to run both services (for simple deployment)
# In production, use separate containers
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
# end file
