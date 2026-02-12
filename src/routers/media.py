import os
import uuid
import base64
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool

from src.config import DOWNLOADS_DIR
from src.services.downloader import get_link_info, download_media
from src.schemas.media import InfoRequest, DownloadRequest
from src.utils.helpers import (
    CleanupFileResponse,
    clean_old_downloads,
    clean_text,
    prepare_url
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/info")
async def link_info(item: InfoRequest, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(clean_old_downloads, str(DOWNLOADS_DIR))
    url = prepare_url(str(item.url))

    if "/search" in url.lower():
        raise HTTPException(
            status_code=400,
            detail="Search links are not supported. Copy the link of a specific video."
        )

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


@router.post("/download")
async def download_endpoint(item: DownloadRequest) -> Any:
    try:
        raw_url = str(item.url)

        if "music.youtube.com" in raw_url and item.media_type == "video":
            raise HTTPException(
                status_code=400,
                detail="Video download is not available for YouTube Music links. Please select Audio.",
            )

        url = prepare_url(raw_url)
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

        url_str = prepare_url(str(item.url)).lower()

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
