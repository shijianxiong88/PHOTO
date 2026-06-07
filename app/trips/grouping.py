from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt


MAX_SAME_TRIP_GAP_HOURS = 6
MAX_SAME_TRIP_DISTANCE_KM = 50


@dataclass(frozen=True)
class MediaPoint:
    id: int
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None


@dataclass(frozen=True)
class TripGroup:
    items: list[MediaPoint]
    confidence: float


def distance_km(a: MediaPoint, b: MediaPoint) -> float | None:
    if a.latitude is None or a.longitude is None or b.latitude is None or b.longitude is None:
        return None
    earth_radius_km = 6371.0
    lat1 = radians(a.latitude)
    lat2 = radians(b.latitude)
    delta_lat = radians(b.latitude - a.latitude)
    delta_lon = radians(b.longitude - a.longitude)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))


def should_split(previous: MediaPoint, current: MediaPoint) -> bool:
    if previous.captured_at is None or current.captured_at is None:
        return False
    gap_hours = (current.captured_at - previous.captured_at).total_seconds() / 3600
    distance = distance_km(previous, current)
    if gap_hours > MAX_SAME_TRIP_GAP_HOURS and distance is None:
        return True
    if distance is None:
        return False
    return gap_hours > MAX_SAME_TRIP_GAP_HOURS and distance > MAX_SAME_TRIP_DISTANCE_KM


def confidence_for(items: list[MediaPoint]) -> float:
    has_missing_time = any(item.captured_at is None for item in items)
    has_missing_gps = any(item.latitude is None or item.longitude is None for item in items)
    if has_missing_time:
        return 0.4
    if has_missing_gps:
        return 0.55
    if len(items) == 1:
        return 0.65
    return 0.85


def group_media_points(points: list[MediaPoint]) -> list[TripGroup]:
    ordered = sorted(points, key=lambda item: item.captured_at or datetime.min)
    if not ordered:
        return []

    groups: list[list[MediaPoint]] = [[ordered[0]]]
    for current in ordered[1:]:
        previous = groups[-1][-1]
        if should_split(previous, current):
            groups.append([current])
        else:
            groups[-1].append(current)

    return [TripGroup(items=items, confidence=confidence_for(items)) for items in groups]
