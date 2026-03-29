#!/bin/bash
# Run the fixed backend on port 8001
# This version includes:
# - Shorts URL support (youtube.com/shorts/...)
# - Real YouTube thumbnail and metadata extraction
# - Real download via yt-dlp

cd "$(dirname "$0")/backend"
d:/download/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir . --host 127.0.0.1 --port 8001 --reload
