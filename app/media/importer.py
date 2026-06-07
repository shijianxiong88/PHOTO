from dataclasses import dataclass
from pathlib import Path
import shutil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.media.hash import sha256_file
from app.media.metadata import detect_media_type, extract_metadata
from app.models import MediaFile


@dataclass(frozen=True)
class ImportResult:
    imported_count: int
    skipped_count: int
    failed_count: int


def iter_incoming_files(incoming_dir: Path) -> list[Path]:
    if not incoming_dir.exists():
        return []
    return sorted(path for path in incoming_dir.rglob("*") if path.is_file())


def destination_for(settings: Settings, source: Path, content_hash: str) -> Path:
    suffix = source.suffix.lower()
    return settings.originals_dir / "unknown-date" / f"{content_hash[:16]}{suffix}"


def import_incoming(settings: Settings, session_factory: sessionmaker[Session]) -> ImportResult:
    settings.ensure_directories()
    imported = 0
    skipped = 0
    failed = 0

    with session_factory() as session:
        for source in iter_incoming_files(settings.incoming_dir):
            if detect_media_type(source) is None:
                skipped += 1
                continue

            content_hash = sha256_file(source)
            if session.query(MediaFile).filter_by(content_hash=content_hash).first():
                skipped += 1
                continue

            try:
                metadata = extract_metadata(source)
                destination = destination_for(settings, source, content_hash)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                media = MediaFile(
                    original_path=str(destination),
                    source_path=str(source),
                    content_hash=content_hash,
                    media_type=metadata.media_type,
                    file_size=source.stat().st_size,
                    captured_at=metadata.captured_at,
                    latitude=metadata.latitude,
                    longitude=metadata.longitude,
                    width=metadata.width,
                    height=metadata.height,
                    duration_seconds=metadata.duration_seconds,
                    device_model=metadata.device_model,
                    scan_status="ready",
                )
                session.add(media)
                session.commit()
                imported += 1
            except (OSError, ValueError, IntegrityError):
                session.rollback()
                failed += 1

    return ImportResult(imported_count=imported, skipped_count=skipped, failed_count=failed)
