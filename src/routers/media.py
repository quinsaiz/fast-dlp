import asyncio
import base64
import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from src.core.exceptions import (
    DownloadError,
    LiveStreamNotSupportedError,
    PlaylistNotSupportedError,
    PrivateVideoError,
    UnsupportedURLError,
    VideoUnavailableError,
)
from src.core.limiter import limiter
from src.schemas.media import DownloadRequest, InfoRequest
from src.services.downloader import download_media, get_link_info
from src.utils.helpers import (
    CleanupFileResponse,
    clean_text,
    prepare_url,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/info")
async def link_info(item: InfoRequest) -> dict[str, Any]:
    url = prepare_url(str(item.url))

    if "search_query=" in url.lower() or "/search" in url.lower():
        raise HTTPException(
            status_code=400,
            detail="Search links are not supported. Copy the link of a specific video.",
        )

    try:
        return await run_in_threadpool(get_link_info, url)
    except PlaylistNotSupportedError:
        raise HTTPException(
            status_code=400,
            detail="Playlists are not supported. Please provide a link to a single video.",
        )
    except (PrivateVideoError, VideoUnavailableError, UnsupportedURLError) as e:
        logger.error(f"Info Error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve video information. Please check the link.",
        )
    except DownloadError as e:
        logger.error(f"Info Error: {e}")
        message = (
            "The provided URL is invalid or unreachable."
            if "name or service not known" in str(e).lower()
            else "Could not retrieve video information. Please check the link."
        )
        raise HTTPException(status_code=400, detail=message)


@router.post("/download")
@limiter.limit("5/minute")
async def download_endpoint(request: Request, item: DownloadRequest) -> Any:
    raw_url = str(item.url)

    if "search_query=" in raw_url.lower() or "/search" in raw_url.lower():
        raise HTTPException(
            status_code=400,
            detail="Search links are not supported. Copy the link of a specific video.",
        )

    if "music.youtube.com" in raw_url and item.media_type == "video":
        raise HTTPException(
            status_code=400,
            detail="Video download is not available for YouTube Music links. Please select Audio.",
        )

    url = prepare_url(raw_url)
    request_id = str(uuid.uuid4())[:8]

    try:
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
    except PlaylistNotSupportedError:
        raise HTTPException(
            status_code=400,
            detail="This is a playlist. Please provide a link to a single video.",
        )
    except VideoUnavailableError:
        raise HTTPException(status_code=400, detail="Video is unavailable or deleted.")
    except PrivateVideoError:
        raise HTTPException(status_code=400, detail="This video is private.")
    except UnsupportedURLError:
        raise HTTPException(status_code=400, detail="This website is not supported.")
    except LiveStreamNotSupportedError:
        raise HTTPException(status_code=400, detail="Live streams are not supported.")
    except DownloadError as e:
        logger.error(f"Download Error: {e}")
        raise HTTPException(status_code=400, detail="Download failed.")

    file_path = result["path"]
    if not await asyncio.to_thread(os.path.exists, file_path):
        logger.error(f"Download Error: file not found after download at {file_path}")
        raise HTTPException(status_code=400, detail="Download failed.")

    media_extension = os.path.splitext(file_path)[1]
    clean_title = clean_text(result["title"])
    display_name = f"{clean_title}{media_extension}"

    b64_filename = base64.b64encode(display_name.encode("utf-8")).decode("utf-8")

    response = CleanupFileResponse(
        path=file_path, media_type="application/octet-stream"
    )
    response.headers["X-File-Name"] = b64_filename
    return response
