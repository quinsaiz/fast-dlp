import asyncio
import logging
import os
import re
import time

from fastapi.responses import FileResponse
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)


class CleanupFileResponse(FileResponse):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await super().__call__(scope, receive, send)
        path = self.path if isinstance(self.path, str) else os.fspath(self.path)
        if await asyncio.to_thread(os.path.exists, path):
            try:
                os.remove(path)
                logger.info(f"Successfully removed temporary file: {path}")
            except Exception as e:
                logger.error(f"Error removing file {path}: {e}")


def clean_old_downloads(directory: str, max_age_seconds: int = 3600) -> None:
    if not os.path.exists(directory):
        return

    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if (
            os.path.isfile(file_path)
            and (now - os.path.getmtime(file_path)) > max_age_seconds
        ):
            try:
                os.remove(file_path)
                logger.info(f"Auto-deleted old file: {filename}")
            except Exception as e:
                logger.error(f"Error deleting {filename}: {e}")


def clean_text(text: str) -> str:
    return re.sub(r"[\\/*?<>|]", "_", text).replace('"', "'")


def prepare_url(url: str) -> str:
    return str(url).replace("music.youtube.com", "www.youtube.com")
