from datetime import datetime, timezone
from pathlib import Path

from app.db import create_session_factory, init_database
from app.models import MediaFile, Trip, TripMedia
from app.trips.service import mark_featured, rename_trip


def test_rename_trip_and_mark_featured(tmp_path: Path) -> None:
    session_factory = create_session_factory(f"sqlite:///{tmp_path / 'album.sqlite'}")
    init_database(session_factory)

    with session_factory() as session:
        media = MediaFile(
            original_path="library/originals/photo.jpg",
            source_path="incoming/photo.jpg",
            content_hash="hash",
            media_type="photo",
            file_size=10,
            captured_at=datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc),
            scan_status="ready",
        )
        trip = Trip(title="旧标题", confidence=0.8, status="needs_review")
        trip.media_items.append(TripMedia(media=media, sort_order=1, featured=False))
        session.add(trip)
        session.commit()
        trip_id = trip.id
        media_id = media.id

    rename_trip(session_factory, trip_id, "西湖周末")
    mark_featured(session_factory, trip_id, media_id, True)

    with session_factory() as session:
        trip = session.query(Trip).one()
        assert trip.title == "西湖周末"
        assert trip.media_items[0].featured is True
