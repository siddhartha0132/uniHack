#!/bin/bash
# Production startup script for Render

set -e

echo "🚀 Starting Veritas Backend..."

# Render's working directory is the repo root
# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Start the application
echo "🌐 Starting FastAPI server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT