from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Platform(str, Enum):
    youtube = "youtube"
    tiktok = "tiktok"


class DownloadStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ResolveUrlRequest(BaseModel):
    url: HttpUrl


class VideoFormat(BaseModel):
    id: str
    label: str
    ext: str


class ResolveUrlResponse(BaseModel):
    platform: Platform
    canonical_url: str
    title: str
    thumbnail_url: str
    duration_seconds: int
    formats: list[VideoFormat]


class CreateDownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str = Field(default="mp4-720p")
    agreed_to_terms: bool = Field(default=False)


class CreateDownloadResponse(BaseModel):
    job_id: str
    status: DownloadStatus


class DownloadJobResponse(BaseModel):
    job_id: str
    status: DownloadStatus
    progress: int
    file_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
