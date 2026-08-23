"""
Root entrypoint for Railway and platforms that run python main.py or uvicorn main:app.
"""
import os
import sys
import subprocess
import uvicorn

# Ensure backend folder is in Python path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Run database migrations safely
try:
    subprocess.run(["alembic", "upgrade", "head"], cwd=BACKEND_DIR, check=False)
except Exception as e:
    print(f"Migration note: {e}")

# Import FastAPI app from backend/app/main.py
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
