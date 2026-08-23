#!/bin/bash
# Production startup script for Render

set -e

echo "🚀 Starting Veritas Backend..."

# Run database migrations
echo "📦 Running database migrations..."
cd /app
alembic upgrade head

# Start the application
echo "🌐 Starting FastAPI server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT