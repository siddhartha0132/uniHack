#!/bin/bash
# Production startup script

set -e

echo "🚀 Starting Veritas Backend..."

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head || echo "⚠️ Migration note: continuing..."

# Start the application
echo "🌐 Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}