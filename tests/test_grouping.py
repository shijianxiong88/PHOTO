from datetime import datetime, timedelta, timezone

from app.trips.grouping import MediaPoint, group_media_points


def test_group_media_points_splits_distant_weekend_outings() -> None:
    saturday = datetime(2026, 6, 6, 9, 0, tzinfo=timezone.utc)
    points = [
        MediaPoint(id=1, captured_at=saturday, latitude=30.0, longitude=120.0),
        MediaPoint(id=2, captured_at=saturday + timedelta(hours=1), latitude=30.01, longitude=120.01),
        MediaPoint(id=3, captured_at=saturday + timedelta(hours=8), latitude=31.5, longitude=121.5),
    ]

    groups = group_media_points(points)

    assert [[item.id for item in group.items] for group in groups] == [[1, 2], [3]]
    assert groups[0].confidence > groups[1].confidence


def test_group_media_points_keeps_missing_gps_with_nearby_time() -> None:
    saturday = datetime(2026, 6, 6, 9, 0, tzinfo=timezone.utc)
    points = [
        MediaPoint(id=1, captured_at=saturday, latitude=30.0, longitude=120.0),
        MediaPoint(id=2, captured_at=saturday + timedelta(minutes=20), latitude=None, longitude=None),
    ]

    groups = group_media_points(points)

    assert [[item.id for item in group.items] for group in groups] == [[1, 2]]
    assert groups[0].confidence == 0.55
