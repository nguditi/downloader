from __future__ import annotations

import logging
import re
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from app.models.schemas import Platform, ResolveUrlResponse, VideoFormat

try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None

logger = logging.getLogger(__name__)

YOUTUBE_PATTERNS = [
    re.compile(r"^(https?://)?(www\.)?youtube\.com/watch\?v=([\w-]{11})"),
    re.compile(r"^(https?://)?(youtu\.be)/([\w-]{11})"),
    re.compile(r"^(https?://)?(www\.)?youtube\.com/shorts/([\w-]{11})"),
]

TIKTOK_PATTERNS = [
    re.compile(r"^(https?://)?(www\.)?tiktok\.com/@[\w\.]+/video/\d+"),
    re.compile(r"^(https?://)?vm\.tiktok\.com/[\w]+"),
]


def _url_for_log(url: str) -> str:
    parsed = urlparse(url)
    safe_query = "..." if parsed.query else ""
    return f"{parsed.scheme or 'https'}://{parsed.netloc}{parsed.path}{safe_query}"


def _metadata_snapshot(info: dict) -> dict:
    return {
        "id": info.get("id"),
        "title_present": bool(info.get("title")),
        "thumbnail_present": bool(info.get("thumbnail")),
        "duration": info.get("duration"),
        "extractor": info.get("extractor"),
        "webpage_url": info.get("webpage_url"),
    }


def _youtube_thumbnail(video_id: str | None) -> str:
    if video_id:
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    return "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"


def _looks_like_youtube_bot_block(message: str) -> bool:
    msg = message.lower()
    return "sign in to confirm you're not a bot" in msg or "sign in to confirm you\u2019re not a bot" in msg


def _fetch_youtube_oembed(url: str) -> tuple[str | None, str | None]:
    endpoint = f"https://www.youtube.com/oembed?{urlencode({'url': url, 'format': 'json'})}"
    request = Request(endpoint, headers={"User-Agent": "Mozilla/5.0 (compatible; ClipNestResolver/1.0)"})
    with urlopen(request, timeout=8) as resp:  # nosec B310 - URL is fixed to YouTube oEmbed endpoint.
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("title"), payload.get("thumbnail_url")


def extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from various YouTube URL formats."""
    for pattern in YOUTUBE_PATTERNS:
        match = pattern.match(url)
        if match:
            return match.group(3)
    return None


def detect_platform(url: str) -> Platform | None:
    for pattern in YOUTUBE_PATTERNS:
        if pattern.match(url):
            return Platform.youtube

    for pattern in TIKTOK_PATTERNS:
        if pattern.match(url):
            return Platform.tiktok

    return None


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path
    query = parsed.query

    if query:
        return f"{scheme}://{netloc}{path}?{query}"
    return f"{scheme}://{netloc}{path}"


def resolve_video(url: str) -> ResolveUrlResponse:
    platform = detect_platform(url)
    safe_url = _url_for_log(url)
    logger.info("resolve.start url=%s platform=%s", safe_url, platform.value if platform else None)
    if platform is None:
        logger.warning("resolve.unsupported_url url=%s", safe_url)
        raise ValueError("Unsupported URL. Only YouTube and TikTok links are accepted.")

    canonical_url = canonicalize_url(url)
    logger.info("resolve.canonicalized url=%s canonical=%s", safe_url, canonical_url)

    if platform == Platform.youtube:
        title, thumbnail, duration = _extract_youtube_metadata(url)
    else:
        title, thumbnail, duration = _extract_tiktok_metadata(url)

    response = ResolveUrlResponse(
        platform=platform,
        canonical_url=canonical_url,
        title=title,
        thumbnail_url=thumbnail,
        duration_seconds=duration,
        formats=[
            VideoFormat(id="mp4-720p", label="MP4 720p", ext="mp4"),
            VideoFormat(id="mp4-1080p", label="MP4 1080p", ext="mp4"),
            VideoFormat(id="audio-m4a", label="Audio M4A", ext="m4a"),
        ],
    )
    logger.info(
        "resolve.done platform=%s title_present=%s thumbnail_present=%s duration=%s",
        platform.value,
        bool(response.title),
        bool(response.thumbnail_url),
        response.duration_seconds,
    )
    return response


def _extract_youtube_metadata(url: str) -> tuple[str, str, int]:
    """Extract real YouTube metadata using yt-dlp."""
    if YoutubeDL is None:
        logger.warning("resolve.youtube.ytdlp_missing url=%s", _url_for_log(url))
        return "YouTube Video", "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg", 0

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }
        logger.info("resolve.youtube.extract.start url=%s opts=%s", _url_for_log(url), ydl_opts)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info("resolve.youtube.extract.info snapshot=%s", _metadata_snapshot(info))
            title = info.get("title", "YouTube Video")
            duration = info.get("duration", 0) or 0
            # Fetch high-quality thumbnail
            video_id = extract_youtube_id(url) or info.get("id")
            thumbnail = _youtube_thumbnail(video_id)
            if title == "YouTube Video" or int(duration) == 0:
                logger.warning(
                    "resolve.youtube.partial_metadata url=%s title=%s duration=%s video_id=%s",
                    _url_for_log(url),
                    title,
                    duration,
                    video_id,
                )
            return title, thumbnail, int(duration)
    except Exception as exc:
        logger.exception("resolve.youtube.extract.failed url=%s error=%s", _url_for_log(url), exc)
        message = str(exc)
        video_id = extract_youtube_id(url)
        thumbnail = _youtube_thumbnail(video_id)

        if _looks_like_youtube_bot_block(message):
            logger.warning("resolve.youtube.bot_block_detected url=%s video_id=%s", _url_for_log(url), video_id)
            try:
                title, oembed_thumbnail = _fetch_youtube_oembed(url)
                logger.info(
                    "resolve.youtube.oembed.success url=%s title_present=%s thumbnail_present=%s",
                    _url_for_log(url),
                    bool(title),
                    bool(oembed_thumbnail),
                )
                return title or "YouTube Video", oembed_thumbnail or thumbnail, 0
            except (HTTPError, URLError, TimeoutError, ValueError) as oembed_exc:
                logger.warning(
                    "resolve.youtube.oembed.failed url=%s error=%s",
                    _url_for_log(url),
                    oembed_exc,
                )

        # Generic extractor fallback
        return "YouTube Video", thumbnail, 0


def _extract_tiktok_metadata(url: str) -> tuple[str, str, int]:
    """Extract real TikTok metadata using yt-dlp."""
    if YoutubeDL is None:
        logger.warning("resolve.tiktok.ytdlp_missing url=%s", _url_for_log(url))
        return "TikTok Video", "https://picsum.photos/seed/tiktok/-preview/640/360", 0

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }
        logger.info("resolve.tiktok.extract.start url=%s opts=%s", _url_for_log(url), ydl_opts)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info("resolve.tiktok.extract.info snapshot=%s", _metadata_snapshot(info))
            title = info.get("title", "TikTok Video")
            duration = info.get("duration", 0) or 0
            # Use thumbnail from metadata or fallback
            thumbnail = info.get("thumbnail") or "https://picsum.photos/seed/tiktok-preview/640/360"
            if title == "TikTok Video" or not info.get("thumbnail"):
                logger.warning(
                    "resolve.tiktok.partial_metadata url=%s title=%s duration=%s thumbnail_present=%s",
                    _url_for_log(url),
                    title,
                    duration,
                    bool(info.get("thumbnail")),
                )
            return title, thumbnail, int(duration)
    except Exception as exc:
        logger.exception("resolve.tiktok.extract.failed url=%s error=%s", _url_for_log(url), exc)
        # Fallback on extractor error
        return "TikTok Video", "https://picsum.photos/seed/tiktok-preview/640/360", 0
