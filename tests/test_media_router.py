from unittest.mock import patch

from fastapi.testclient import TestClient

from src.core.exceptions import PlaylistNotSupportedError


def test_info_endpoint_success(client: TestClient) -> None:
    with patch("src.routers.media.get_link_info") as mock_get_info:
        mock_get_info.return_value = {
            "title": "Test Video",
            "author": "Test Channel",
            "duration": 120,
            "thumbnail": "https://example.com/thumb.jpg",
            "url": "https://youtube.com/watch?v=test",
            "available_qualities": [1080, 720],
            "is_live": False,
            "allowed_bitrates": [320, 256, 128],
        }
        response = client.post(
            "/info",
            json={"url": "https://youtube.com/watch?v=test"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Test Video"


def test_info_endpoint_rejects_search_links(client: TestClient) -> None:
    response = client.post(
        "/info",
        json={"url": "https://youtube.com/results?search_query=test"},
    )
    assert response.status_code == 400


def test_info_endpoint_playlist_error(client: TestClient) -> None:
    with patch("src.routers.media.get_link_info") as mock_get_info:
        mock_get_info.side_effect = PlaylistNotSupportedError("playlist")
        response = client.post(
            "/info",
            json={"url": "https://youtube.com/playlist?list=test"},
        )

    assert response.status_code == 400
    assert "Playlist" in response.json()["detail"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
