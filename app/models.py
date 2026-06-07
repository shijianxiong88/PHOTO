from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MediaFile(Base):
    __tablename__ = "media_files"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_media_files_content_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_path: Mapped[str] = mapped_column(String(1024))
    source_path: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    media_type: Mapped[str] = mapped_column(String(32))
    file_size: Mapped[int] = mapped_column(Integer)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(256), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    scan_status: Mapped[str] = mapped_column(String(32), default="pending")
    scan_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    trip_links: Mapped[list["TripMedia"]] = relationship(back_populates="media")


class Place(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="manual")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    primary_place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="needs_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    primary_place: Mapped[Place | None] = relationship()
    media_items: Mapped[list["TripMedia"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripMedia.sort_order",
    )


class TripMedia(Base):
    __tablename__ = "trip_media"
    __table_args__ = (UniqueConstraint("trip_id", "media_id", name="uq_trip_media"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"))
    media_id: Mapped[int] = mapped_column(ForeignKey("media_files.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped[Trip] = relationship(back_populates="media_items")
    media: Mapped[MediaFile] = relationship(back_populates="trip_links")


class UserEdit(Base):
    __tablename__ = "user_edits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
