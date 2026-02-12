from typing import Literal
from pydantic import BaseModel, HttpUrl

class InfoRequest(BaseModel):
    url: HttpUrl

class DownloadRequest(InfoRequest):
    media_type: Literal["video", "audio"] = "video"
    video_codec: Literal["mp4", "webm"] = "mp4"
    quality: Literal["1080", "720", "480", "360"] = "1080"
    audio_codec: Literal["mp3", "m4a", "opus", "wav"] = "mp3"
    bitrate: Literal["320", "256", "128"] = "256"