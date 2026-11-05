"""
UZEX AI Assistant - Streamlit Web App Runner
"""
import sys
import os
import subprocess

if __name__ == '__main__':
    web_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'web_app.py')
    python_exe = sys.executable
    cmd = [python_exe, "-m", "streamlit", "run", web_app_path, "--server.port=8501", "--server.headless=false"]
    print(f"Starting Streamlit app: {' '.join(cmd)}")
    subprocess.run(cmd)
