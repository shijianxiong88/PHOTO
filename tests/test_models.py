from datetime import datetime, timezone
from pathlib import Path

from app.db import create_session_factory, init_database
from app.models import MediaFile, Trip, TripMedia


def test_database_persists_media_and_trip(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'album.sqlite'}"
    session_factory = create_session_factory(db_url)
    init_database(session_factory)

    with session_factory() as session:
        media = MediaFile(
            original_path="library/originals/2026/06/photo.jpg",
            source_path="incoming/photo.jpg",
            content_hash="abc123",
            media_type="photo",
            file_size=1024,
            captured_at=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc),
            latitude=30.2741,
            longitude=120.1551,
            scan_status="ready",
        )
        trip = Trip(
            title="2026-06-06 周末出游",
            start_at=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 6, 6, 18, 0, tzinfo=timezone.utc),
            confidence=0.8,
            status="needs_review",
        )
        trip.media_items.append(TripMedia(media=media, sort_order=1, featured=True))
        session.add(trip)
        session.commit()

    with session_factory() as session:
        stored = session.query(Trip).one()
        assert stored.title == "2026-06-06 周末出游"
        assert stored.media_items[0].media.content_hash == "abc123"
        assert stored.media_items[0].featured is True
