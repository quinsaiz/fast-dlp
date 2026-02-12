# fast-dlp

A lightweight, asynchronous web application for analyzing and downloading YouTube media. This tool allows users to extract video or audio in various formats and qualities, ensuring high compatibility with media players through optimized encoding.

## Features

- **Media Analysis**: Retrieve video metadata including title, author, duration, and available qualities before downloading.
- **Video Downloads**: Support for MP4 (H.264/AVC) and WebM formats with quality selection up to 1080p.
- **Audio Extraction**: Convert videos to MP3, M4A, Opus, or WAV with selectable bitrates.
- **Automatic Cleanup**: Temporary files are automatically removed from the server after the download is completed.

## Tech Stack

- **Backend**: Python 3.x, FastAPI
- **Media Engine**: yt-dlp, FFmpeg
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Schema Validation**: Pydantic

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg installed and added to the system PATH.

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/quinsaiz/fast-dlp.git
   cd fast-dlp
   ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:
    ```bash
    uvicorn src.main:src --reload
    ```

### Docker Deployment (Recommended)

For a simplified setup that includes all system dependencies like FFmpeg automatically:

1. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

## Project Structure
```bash
fast-dlp/
├── src/
│   ├── downloader.py  # Media extraction logic using yt-dlp
│   └── main.py        # FastAPI routes and middleware
├── static/
│   ├── index.html     # Frontend structure
│   ├── index.js       # Asynchronous UI logic
│   └── index.css      # Styling
├── downloads/         # Temporary storage (auto-cleaned)
└── requirements.txt
```

## License

This project is open-source and available under the MIT License.