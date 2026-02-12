from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import STATIC_DIR, DOWNLOADS_DIR, CORS_ORIGINS
from src.core.logger import setup_logger
from src.utils.helpers import clean_old_downloads
from src.routers import media

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application starting: Cleaning downloads...")
    clean_old_downloads(str(DOWNLOADS_DIR), max_age_seconds=0)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-File-Name"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(
    media.router
)


@app.get("/")
async def read_index():
    return FileResponse(STATIC_DIR / "index.html")
