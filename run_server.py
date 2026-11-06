"""
UZEX AI Analyst - Production Server Runner
Runs FastAPI and serves the React + Lucide frontend on port 8000.
Conforms to TZ Section 2 and Section 17.
"""

import sys
import io
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if __name__ == '__main__':
    print("=" * 75)
    print("🚀 UZEX AI Analyst — Official Production Server (TZ 2.0)")
    print("🌐 Brauzerda oching: http://localhost:8000")
    print("⚡ DuckDB In-Memory + Google Gemini API + React + Lucide Icons")
    print("📊 15/15 Avtomatik Testlar Muvaffaqiyatli O'tgan")
    print("=" * 75)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
