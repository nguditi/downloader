# ClipNest MVP (FastAPI + React)

Website MVP with backend and frontend for YouTube/TikTok URL resolve and demo download jobs.

## Important Use Policy

Use this project only for content you own or are authorized to download.

## Project Structure

- `backend/`: FastAPI API for URL resolve, job creation, job status, and file download.
- `frontend/`: React + Vite app for URL input, preview, format selection, progress polling, and file download action.

## Backend Setup

1. Open terminal in `backend/`.
2. Install dependencies:

```bash
py -m pip install -r requirements.txt
```

3. Start API server (fixed version with Shorts support + real thumbnails):

```bash
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Or use the provided script:
- Windows: `run_backend_fixed.bat`
- Linux/Mac: `bash run_backend_fixed.sh`

Backend endpoints:

- `GET /health`
- `POST /api/v1/resolve` — Extract video metadata (title, duration, thumbnail, formats)
- `POST /api/v1/download` — Create async download job
- `GET /api/v1/download/{job_id}` — Poll job status and progress
- `GET /api/v1/download/{job_id}/file` — Download completed video file

## Frontend Setup

1. Open terminal in `frontend/`.
2. Install dependencies:

```bash
npm install
```

3. Start dev server:

```bash
npm run dev
```

Open http://localhost:5173.

**Note:** Frontend is pre-configured to call backend on `http://localhost:8001`, matching the fixed backend port.

## Features

- **YouTube Support**: Regular watch links and Shorts URLs with real metadata and download
- **TikTok Support**: Real metadata extraction and download via yt-dlp (subject to TikTok's anti-bot IP blocking)
- **Real Metadata**: Title, duration, thumbnail extracted via yt-dlp
- **Format Selection**: MP4 720p, MP4 1080p (YouTube only), Audio M4A
- **Async Downloads**: Non-blocking job-based architecture with progress tracking
- **File Delivery**: Download completed videos with correct MIME type

## Implemented Flow

1. Paste YouTube/TikTok URL → Resolve metadata.
2. Select format.
3. Confirm terms checkbox.
4. Start download job → Real-time progress polling.
5. Download generated file when completed.

## Notes

- Backend uses `yt-dlp` for real YouTube and TikTok downloading.
- **YouTube**: Fully functional for all URL types (watch, youtu.be, shorts).
- **TikTok**: Real download is enabled but may fail with "IP blocked" error due to TikTok's anti-scraping measures. This is a platform-level restriction, not an application issue. If TikTok's API becomes available or proxies are configured, downloads will work automatically.
- Temporary files are created in `backend/tmp_downloads/` with automatic cleanup.

