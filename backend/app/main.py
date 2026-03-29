from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.download import router as download_router
from app.routers.health import router as health_router

app = FastAPI(
    title="Video Downloader MVP API",
    version="0.1.0",
    description="MVP API for resolving and downloading user-authorized YouTube/TikTok content.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(download_router)
