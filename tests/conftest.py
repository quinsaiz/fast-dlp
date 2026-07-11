from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_ydl_info() -> dict[str, Any]:
    return {
        "title": "Test Video",
        "uploader": "Test Channel",
        "duration": 120,
        "thumbnail": "https://example.com/thumb.jpg",
        "formats": [{"height": 1080}, {"height": 720}, {"height": 360}],
        "is_live": False,
    }
