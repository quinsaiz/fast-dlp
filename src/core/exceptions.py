class DownloadError(Exception):
    pass


class UnsupportedURLError(DownloadError):
    pass


class PlaylistNotSupportedError(DownloadError):
    pass


class VideoUnavailableError(DownloadError):
    pass


class PrivateVideoError(DownloadError):
    pass


class LiveStreamNotSupportedError(DownloadError):
    pass
