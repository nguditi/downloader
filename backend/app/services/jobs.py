from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import DownloadJobResponse, DownloadStatus

try:
    from yt_dlp import YoutubeDL
except ImportError:  # pragma: no cover
    YoutubeDL = None


def _get_temp_dir() -> Path:
    # Vercel serverless filesystem is read-only except /tmp.
    if os.getenv("VERCEL"):
        return Path("/tmp") / "tmp_downloads"
    return Path(tempfile.gettempdir()) / "clipnest_tmp_downloads"


@dataclass
class JobState:
    job_id: str
    status: DownloadStatus
    progress: int
    file_name: str | None
    file_path: Path | None
    created_at: datetime
    updated_at: datetime
    error: str | None = None


_JOBS: dict[str, JobState] = {}


def create_job(file_ext: str) -> JobState:
    job_id = uuid4().hex
    now = datetime.utcnow()
    state = JobState(
        job_id=job_id,
        status=DownloadStatus.queued,
        progress=0,
        file_name=f"video_{job_id[:8]}.{file_ext}",
        file_path=None,
        created_at=now,
        updated_at=now,
    )
    _JOBS[job_id] = state
    return state


def get_job(job_id: str) -> JobState | None:
    return _JOBS.get(job_id)


def to_response(state: JobState) -> DownloadJobResponse:
    return DownloadJobResponse(
        job_id=state.job_id,
        status=state.status,
        progress=state.progress,
        file_name=state.file_name,
        created_at=state.created_at,
        updated_at=state.updated_at,
        error=state.error,
    )


async def run_fake_download(job_id: str, source_url: str, platform: str, format_id: str) -> None:
    state = _JOBS[job_id]
    state.status = DownloadStatus.processing
    state.updated_at = datetime.utcnow()

    try:
        if YoutubeDL is None:
            raise RuntimeError("Missing dependency: yt-dlp. Run 'py -m pip install -r requirements.txt'.")

        # Format maps per platform
        youtube_format_map = {
            "mp4-720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
            "mp4-1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
            "audio-m4a": "bestaudio[ext=m4a]/bestaudio",
        }
        tiktok_format_map = {
            "mp4-720p": "best[ext=mp4]/best",
            "mp4-1080p": "best[ext=mp4]/best",  # TikTok doesn't have 1080p; will fallback to best
            "audio-m4a": "best[ext=m4a]/bestaudio/best",
        }

        format_map = youtube_format_map if platform == "youtube" else tiktok_format_map
        selected_format = format_map.get(format_id)
        if selected_format is None:
            raise RuntimeError(f"Unsupported format: {format_id}")

        temp_dir = _get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str((temp_dir / f"{job_id}.%(ext)s").resolve())

        def progress_hook(data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                total_bytes = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded_bytes = data.get("downloaded_bytes", 0)
                if isinstance(total_bytes, int) and total_bytes > 0:
                    pct = int((downloaded_bytes / total_bytes) * 100)
                    state.progress = max(1, min(99, pct))
                else:
                    state.progress = max(1, min(99, state.progress + 1))
                state.updated_at = datetime.utcnow()
            elif status == "finished":
                state.progress = 99
                state.updated_at = datetime.utcnow()

        ydl_opts = {
            "format": selected_format,
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
        }

        def _download() -> tuple[str, str]:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source_url, download=True)
                downloaded_path = ydl.prepare_filename(info)
                ext = info.get("ext", "mp4")
                return downloaded_path, ext

        downloaded_path, ext = await asyncio.to_thread(_download)

        final_path = Path(downloaded_path)
        if not final_path.exists():
            matches = sorted(temp_dir.glob(f"{job_id}.*"))
            if not matches:
                raise RuntimeError("Download finished but output file not found.")
            final_path = matches[0]
            ext = final_path.suffix.lstrip(".") or ext

        state.file_path = final_path
        state.file_name = f"video_{job_id[:8]}.{ext}"
        state.status = DownloadStatus.completed
        state.progress = 100
        state.updated_at = datetime.utcnow()
    except Exception as exc:  # pragma: no cover
        state.status = DownloadStatus.failed
        state.error = str(exc)
        state.updated_at = datetime.utcnow()
