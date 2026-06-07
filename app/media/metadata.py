from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import mimetypes


PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


@dataclass(frozen=True)
class MediaMetadata:
    media_type: str
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    device_model: str | None


def detect_media_type(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in PHOTO_EXTENSIONS:
        return "photo"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type and mime_type.startswith("image/"):
        return "photo"
    if mime_type and mime_type.startswith("video/"):
        return "video"
    return None


def extract_metadata(path: Path) -> MediaMetadata:
    media_type = detect_media_type(path)
    if media_type is None:
        raise ValueError(f"unsupported media file: {path}")
    return MediaMetadata(
        media_type=media_type,
        captured_at=None,
        latitude=None,
        longitude=None,
        width=None,
        height=None,
        duration_seconds=None,
        device_model=None,
    )
