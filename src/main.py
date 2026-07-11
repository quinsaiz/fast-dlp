import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.core.limiter import limiter
from src.core.logger import setup_logger
from src.routers import health, media
from src.utils.helpers import clean_old_downloads

logger = setup_logger(__name__)


async def _periodic_cleanup() -> None:
    while True:
        await asyncio.sleep(settings.cleanup_interval_seconds)
        await asyncio.to_thread(
            clean_old_downloads,
            str(settings.downloads_dir),
            settings.max_file_age_seconds,
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Application starting: Cleaning downloads...")
    clean_old_downloads(str(settings.downloads_dir), max_age_seconds=0)
    cleanup_task = asyncio.create_task(_periodic_cleanup())
    yield
    cleanup_task.cancel()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-File-Name"],
)

app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

app.include_router(health.router)
app.include_router(media.router)


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(settings.static_dir / "index.html")
