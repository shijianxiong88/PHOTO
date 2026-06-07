from sqlalchemy.orm import Session, sessionmaker

from app.models import Trip, TripMedia, UserEdit


def rename_trip(session_factory: sessionmaker[Session], trip_id: int, title: str) -> None:
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("trip title cannot be empty")
    with session_factory() as session:
        trip = session.get(Trip, trip_id)
        if trip is None:
            raise ValueError(f"trip not found: {trip_id}")
        trip.title = clean_title
        session.add(UserEdit(entity_type="trip", entity_id=trip_id, action="rename", details=clean_title))
        session.commit()


def mark_featured(
    session_factory: sessionmaker[Session],
    trip_id: int,
    media_id: int,
    featured: bool,
) -> None:
    with session_factory() as session:
        link = (
            session.query(TripMedia)
            .filter(TripMedia.trip_id == trip_id, TripMedia.media_id == media_id)
            .one_or_none()
        )
        if link is None:
            raise ValueError(f"media {media_id} is not in trip {trip_id}")
        link.featured = featured
        session.add(
            UserEdit(
                entity_type="trip_media",
                entity_id=link.id,
                action="mark_featured",
                details=str(featured).lower(),
            )
        )
        session.commit()
