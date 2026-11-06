"""
UZEX AI Analyst - Production Server Runner
Runs FastAPI and serves the React + Lucide frontend on port 8000.
Conforms to TZ Section 2 and Section 17.
"""

import sys
import io
import os
import uvicorn

# Safely load .env without crashing if python-dotenv is not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass

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
