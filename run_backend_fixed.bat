@echo off
REM Run the fixed backend on port 8001
REM This version includes:
REM - Shorts URL support (youtube.com/shorts/...)
REM - Real YouTube thumbnail and metadata extraction
REM - Real download via yt-dlp

cd /d "%~dp0backend"
d:/download/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir . --host 127.0.0.1 --port 8001 --reload
