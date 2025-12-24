FROM python:3.11-slim

# Set timezone for cron
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Setup cron job
COPY crontab /etc/cron.d/newsletter-cron
RUN chmod 0644 /etc/cron.d/newsletter-cron && \
    crontab /etc/cron.d/newsletter-cron

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD test -f /app/logs/health.txt || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
