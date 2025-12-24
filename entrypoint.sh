#!/bin/bash
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Mortgage AI Newsletter container..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Timezone: $TZ"

# Export environment variables for cron
printenv | grep -E "^(NEWSAPI|NANOGPT|PUSHBULLET|GITHUB|LOG_LEVEL|RSS|LOG_DIR)" >> /etc/environment

# Create logs directory if not exists
mkdir -p /app/logs
chmod 777 /app/logs

# Initial health check file
date > /app/logs/health.txt

# Optionally run newsletter immediately on first start (for testing)
if [ "${RUN_ON_START:-false}" = "true" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running newsletter immediately (RUN_ON_START=true)..."
    cd /app && /usr/local/bin/python -m src.main
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting cron daemon..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Newsletter scheduled for 9:00 AM EST daily"

# Start cron in foreground
exec cron -f
