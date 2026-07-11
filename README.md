# fast-dlp

A lightweight, asynchronous web application for analyzing and downloading YouTube media. This tool allows users to
extract video or audio in various formats and qualities, ensuring high compatibility with media players through
optimized encoding.

## Features

- **Media Analysis**: Retrieve video metadata including title, author, duration, and available qualities before
  downloading.
- **Video Downloads**: Support for MP4 (H.264/AVC) and WebM formats with quality selection up to 1080p.
- **Audio Extraction**: Convert videos to MP3, M4A, Opus, or WAV with selectable bitrates.
- **Rate Limiting & Security**: Built-in protection using `slowapi` to prevent abuse of the download endpoints.
- **Automatic Cleanup**: Temporary files are automatically tracked and removed from the server via async background
  tasks after delivery.
- **Health Monitoring**: Integrated `/health` endpoint for Docker and orchestration healthchecks.

## Tech Stack

- **Backend**: Python 3.13+, FastAPI
- **Environment & Package Management**: [uv](https://github.com/astral-sh/uv)
- **Configuration**: Pydantic Settings
- **Media Engine**: `yt-dlp` (with Deno integration inside Docker), FFmpeg
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Code Quality**: Ruff (Linting & Formatting), Mypy (Static Type Checking)
- **Testing**: Pytest

## Installation & Setup

### Local Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/quinsaiz/fast-dlp.git && \
    cd fast-dlp
    ```

2. **Configure environment variables:**
   Copy the example environment file and adjust values if necessary:

    ```bash
    cp .env.example .env
    ```

3. **Install dependencies & create virtual environment:**
   `uv` will automatically create a `.venv` and sync your dependencies exactly as locked in `uv.lock`:

    ```bash
    uv sync
    ```

4. **Run the application locally:**

    ```bash
    uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ```

---

### Docker Deployment (Recommended)

The project includes a multi-stage Dockerfile optimized for cached builds using `uv` and production-ready security (
running under a non-root `appuser`).

#### Production Mode

To run the production container (without live code reloading):

```bash
docker-compose up -d --build
```

#### Development Mode (With Live Reload & Volume Mounts)

The project includes a `docker-compose.override.yml` that mounts your local `src` and `static` folders directly inside
the container and enables hot-reloading:

---

## Testing & Code Quality

**Run Unit Tests:**

```bash
uv run pytest
```

**Run Code Linters & Formatters (Ruff):**

```bash
uv run ruff check .
uv run ruff format .
```

**Run Type Checking (Mypy):**

```bash
uv run mypy .
```

---

## Project Structure

```bash
.
├── docker-compose.override.yml  # Dev-specific docker compose configuration
├── docker-compose.yml           # Base production docker compose services
├── Dockerfile                   # Multi-stage build leveraging uv and non-root execution
├── entrypoint.sh                # Smart execution script handling reload flags
├── LICENSE
├── pyproject.toml               # Project metadata and dependencies (PEP 621)
├── README.md
├── src/
│   ├── config.py                # Base Settings and configuration module
│   ├── main.py                  # FastAPI initialization and lifespan events
│   ├── core/
│   │   ├── exceptions.py        # Structured custom exception classes
│   │   ├── limiter.py           # Slowapi rate-limiter setup
│   │   └── logger.py            # Unified application logging
│   ├── routers/
│   │   ├── health.py            # Health monitoring route
│   │   └── media.py             # Download and extraction endpoints
│   ├── schemas/
│   │   └── media.py             # Pydantic schemas for request validation
│   ├── services/
│   │   └── downloader.py        # Media extraction core logic wrapping yt-dlp
│   └── utils/
│       └── helpers.py           # Text cleaners and path transformers
├── static/                      # Static UI hosting directory
│   ├── index.css
│   ├── index.html
│   └── index.js
├── tests/                       # Automated test suite (Pytest)
│   ├── conftest.py
│   ├── test_downloader.py
│   └── test_media_router.py
└── uv.lock                      # Fully reproducible dependency lockfile

```

## License

This project is open-source and available under the [MIT License](https://github.com/quinsaiz/fast-dlp/blob/main/LICENSE).
