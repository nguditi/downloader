from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import CreateDownloadRequest, CreateDownloadResponse, DownloadJobResponse
from app.services.jobs import create_job, get_job, run_fake_download, to_response
from app.services.resolver import resolve_video

router = APIRouter(prefix="/api/v1", tags=["download"])
logger = logging.getLogger(__name__)


@router.post("/resolve", response_model=dict)
def resolve_url(payload: dict) -> dict:
    trace_id = uuid4().hex[:8]
    url = payload.get("url")
    if not isinstance(url, str) or not url:
        logger.warning("resolve.request.invalid trace_id=%s payload_keys=%s", trace_id, list(payload.keys()))
        raise HTTPException(status_code=400, detail="Field 'url' is required")

    try:
        logger.info("resolve.request.start trace_id=%s url=%s", trace_id, url)
        result = resolve_video(url)
        logger.info(
            "resolve.request.success trace_id=%s platform=%s title_present=%s thumbnail_present=%s duration=%s",
            trace_id,
            result.platform.value,
            bool(result.title),
            bool(result.thumbnail_url),
            result.duration_seconds,
        )
        return result.model_dump()
    except ValueError as exc:
        logger.warning("resolve.request.failed trace_id=%s error=%s", trace_id, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/download", response_model=CreateDownloadResponse)
async def create_download(payload: CreateDownloadRequest) -> CreateDownloadResponse:
    if not payload.agreed_to_terms:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the terms. Only download content you own or are allowed to use.",
        )

    try:
        resolved = resolve_video(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    selected = next((f for f in resolved.formats if f.id == payload.format_id), None)
    if selected is None:
        raise HTTPException(status_code=400, detail="Invalid format_id")

    state = create_job(selected.ext)
    asyncio.create_task(
        run_fake_download(
            state.job_id,
            source_url=resolved.canonical_url,
            platform=resolved.platform.value,
            format_id=payload.format_id,
        )
    )

    return CreateDownloadResponse(job_id=state.job_id, status=state.status)


@router.get("/download/{job_id}", response_model=DownloadJobResponse)
def get_download_status(job_id: str) -> DownloadJobResponse:
    state = get_job(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return to_response(state)


@router.get("/download/{job_id}/file")
def get_download_file(job_id: str) -> FileResponse:
    state = get_job(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if state.file_path is None or not state.file_path.exists():
        raise HTTPException(status_code=409, detail="File is not ready")

    return FileResponse(path=state.file_path, filename=state.file_name, media_type="application/octet-stream")
