import os
import re
import time
import uuid
import base64
import logging
from typing import Any, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl

from app.downloader import get_link_info, download_media

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

static_path = os.path.join(os.path.dirname(__file__), "..", "static")
downloads_path = os.path.join(os.path.dirname(__file__), "..", "downloads")

for path in [static_path, downloads_path]:
    if not os.path.exists(path):
        os.makedirs(path)


class CleanupFileResponse(FileResponse):
    async def __call__(self, scope, receive, send):
        await super().__call__(scope, receive, send)
        if os.path.exists(self.path):
            try:
                os.remove(self.path)
                logger.info(f"Successfully removed temporary file: {self.path}")
            except Exception as e:
                logger.error(f"Error removing file {self.path}: {e}")


def clean_old_downloads(directory: str, max_age_seconds: int = 3600):
    if not os.path.exists(directory):
        return

    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            if (now - os.path.getmtime(file_path)) > max_age_seconds:
                try:
                    os.remove(file_path)
                    logger.info(f"Auto-deleted old file: {filename}")
                except Exception as e:
                    logger.error(f"Error deleting {filename}: {e}")


def clean_text(text: str) -> str:
    return re.sub(r"[\\/*?<>|]", "_", text).replace('"', "'")


def prepare_url(url: Any) -> str:
    return str(url).replace("music.youtube.com", "www.youtube.com")


class InfoRequest(BaseModel):
    url: HttpUrl


class DownloadRequest(InfoRequest):
    media_type: Literal["video", "audio"] = "video"
    video_codec: Literal["mp4", "webm"] = "mp4"
    quality: Literal["1080", "720", "480"] = "1080"
    audio_codec: Literal["mp3", "m4a", "opus", "wav"] = "mp3"
    bitrate: Literal["320", "256", "128"] = "256"


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application starting: Cleaning downloads...")
    clean_old_downloads(downloads_path, max_age_seconds=0)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-File-Name"],
)

app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    )


@app.post("/info")
async def link_info(item: InfoRequest, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(clean_old_downloads, downloads_path)
    url = prepare_url(item.url)

    if "/search" in url.lower():
        raise HTTPException(status_code=400,
                            detail="Search links are not supported. Copy the link of a specific video.")

    try:
        return await run_in_threadpool(get_link_info, url)
    except Exception as e:
        error_str = str(e)
        logger.error(f"Info Error: {error_str}")

        if "playlist" in error_str.lower():
            message = "Playlists are not supported. Please provide a link to a single video."
        elif "Name or service not known" in error_str:
            message = "The provided URL is invalid or unreachable."
        else:
            message = "Could not retrieve video information. Please check the link."

        raise HTTPException(status_code=400, detail=message)


@app.post("/download")
async def download_endpoint(item: DownloadRequest) -> Any:
    try:
        raw_url = str(item.url)

        if "music.youtube.com" in raw_url and item.media_type == "video":
            raise HTTPException(
                status_code=400,
                detail="Video download is not available for YouTube Music links. Please select Audio.",
            )

        url = prepare_url(item.url)
        request_id = str(uuid.uuid4())[:8]

        result = await run_in_threadpool(
            download_media,
            url=url,
            media_type=item.media_type,
            video_codec=item.video_codec,
            quality=item.quality,
            audio_codec=item.audio_codec,
            bitrate=item.bitrate,
            request_id=request_id,
        )

        file_path = result["path"]
        if not os.path.exists(file_path):
            raise Exception("File was not found after download")

        media_extension = os.path.splitext(file_path)[1]
        clean_title = clean_text(result["title"])
        display_name = f"{clean_title}{media_extension}"

        b64_filename = base64.b64encode(display_name.encode("utf-8")).decode("utf-8")

        response = CleanupFileResponse(
            path=file_path, media_type="application/octet-stream"
        )

        response.headers["X-File-Name"] = b64_filename
        return response

    except Exception as e:
        error_str = str(e)
        logger.error(f"Download Error: {error_str}")

        url_str = prepare_url(item.url).lower()

        if "search" in url_str:
            error_msg = "Search links are not supported. Copy the link of a specific video."
        elif "playlist" in error_str.lower():
            error_msg = "This is a playlist. Please provide a link to a single video."
        elif "video unavailable" in error_str.lower():
            error_msg = "Video is unavailable or deleted."
        elif "private video" in error_str.lower():
            error_msg = "This video is private."
        elif "unsupported url" in error_str.lower():
            error_msg = "This website is not supported."
        else:
            error_msg = "Download failed."

        raise HTTPException(status_code=400, detail=error_msg)
