import os
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from src.config import settings
from src.core.exceptions import (
    DownloadError,
    LiveStreamNotSupportedError,
    PlaylistNotSupportedError,
    PrivateVideoError,
    UnsupportedURLError,
    VideoUnavailableError,
)


def get_downloads_dir() -> str:
    return str(settings.downloads_dir)


def get_link_info(url: str) -> dict[str, Any]:
    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "socket_timeout": 10,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
        try:
            info = ydl.extract_info(url, download=False)
        except YtDlpDownloadError as e:
            raise _map_yt_dlp_error(str(e)) from e

        allowed_heights = {1080, 720, 480, 360}
        formats = info.get("formats") or []
        available_qualities = set()
        for f in formats:
            h = f.get("height")
            if h in allowed_heights:
                available_qualities.add(h)

        sorted_qualities = sorted(list(available_qualities), reverse=True)

        return {
            "title": info.get("title"),
            "author": info.get("uploader"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "url": url,
            "available_qualities": sorted_qualities,
            "is_live": info.get("is_live", False),
            "allowed_bitrates": [320, 256, 128],
        }


def download_media(
    url: str,
    media_type: str = "video",
    video_codec: str = "mp4",
    quality: str = "1080",
    audio_codec: str = "mp3",
    bitrate: str = "256",
    request_id: str = "",
) -> dict[str, Any]:
    downloads_dir = get_downloads_dir()
    prefix = f"{request_id}_" if request_id else ""
    filename_format = f"{prefix}%(title)s [%(id)s].%(ext)s"

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 15,
        "outtmpl": os.path.join(downloads_dir, filename_format),
    }

    if media_type == "audio":
        extension = audio_codec
        supports_thumbnail = audio_codec in ("mp3", "m4a", "opus")

        postprocessors = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_codec,
                "preferredquality": bitrate,
            },
            {"key": "FFmpegMetadata", "add_metadata": True},
        ]
        if supports_thumbnail:
            postprocessors.append({"key": "EmbedThumbnail"})

        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "writethumbnail": supports_thumbnail,
                "postprocessors": postprocessors,
            }
        )
    else:
        extension = "mp4" if video_codec == "mp4" else "webm"

        if video_codec == "mp4":
            v_format = f"bestvideo[height<={quality}][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            v_format = f"bestvideo[height<={quality}]+bestaudio/best"

        ydl_opts.update(
            {
                "format": v_format,
                "merge_output_format": extension,
                "postprocessors": [
                    {"key": "FFmpegMetadata", "add_metadata": True},
                ],
            }
        )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
        try:
            info = ydl.extract_info(url, download=True)
        except YtDlpDownloadError as e:
            raise _map_yt_dlp_error(str(e)) from e

        if info.get("is_live"):
            raise LiveStreamNotSupportedError("Live streams are not supported")

        actual_path = ydl.prepare_filename(info)

        base_no_ext = os.path.splitext(actual_path)[0]
        final_file = f"{base_no_ext}.{extension}"

        if os.path.exists(final_file):
            actual_path = final_file

        title = info.get("title") or "media"
        author = info.get("uploader") or info.get("channel") or info.get("artist")

        if author and title and author.lower() not in title.lower():
            full_title = f"{author} - {title}"
        else:
            full_title = title if title else "media"

        return {"path": actual_path, "title": full_title}


def _map_yt_dlp_error(error_str: str) -> DownloadError:
    lowered = error_str.lower()
    if "playlist" in lowered:
        return PlaylistNotSupportedError(error_str)
    if "private video" in lowered:
        return PrivateVideoError(error_str)
    if "video unavailable" in lowered:
        return VideoUnavailableError(error_str)
    if "unsupported url" in lowered:
        return UnsupportedURLError(error_str)
    return DownloadError(error_str)
