from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yt_dlp

from src.core.exceptions import PlaylistNotSupportedError, VideoUnavailableError
from src.services.downloader import get_link_info


@patch("src.services.downloader.yt_dlp.YoutubeDL")
def test_get_link_info_returns_expected_shape(
    mock_ydl_cls: MagicMock,
    mock_ydl_info: dict[str, Any],
) -> None:
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = mock_ydl_info
    mock_ydl_cls.return_value.__enter__.return_value = mock_instance

    result = get_link_info("https://youtube.com/watch?v=test")

    assert result["title"] == "Test Video"
    assert result["available_qualities"] == [1080, 720, 360]
    assert result["is_live"] is False


@patch("src.services.downloader.yt_dlp.YoutubeDL")
def test_get_link_info_raises_playlist_error(mock_ydl_cls: MagicMock) -> None:
    mock_instance = MagicMock()
    mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError(
        "This playlist is not supported"
    )
    mock_ydl_cls.return_value.__enter__.return_value = mock_instance

    with pytest.raises(PlaylistNotSupportedError):
        get_link_info("https://youtube.com/playlist?list=test")


@patch("src.services.downloader.yt_dlp.YoutubeDL")
def test_get_link_info_raises_video_unavailable(mock_ydl_cls: MagicMock) -> None:
    mock_instance = MagicMock()
    mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError(
        "Video unavailable"
    )
    mock_ydl_cls.return_value.__enter__.return_value = mock_instance

    with pytest.raises(VideoUnavailableError):
        get_link_info("https://youtube.com/watch?v=deleted")
