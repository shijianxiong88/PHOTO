# Family Trip Album System Design

## Purpose

Build a home-server system for managing family weekend photos and videos. The first version focuses on automatically grouping imported media into trip records so the family can remember where they went, when they went, and which photos and videos belong together.

The system will run on an Ubuntu laptop used as a home server. Access starts inside the home LAN only. External access, automatic phone sync, richer album presentation, and AI-generated travel journals can be added after the core organizing flow is reliable.

## First-Version Scope

The first version includes:

- Manual import from phones or cameras into an `incoming/` folder.
- Media scanning for photo and video files.
- Metadata extraction for capture time, GPS coordinates, file type, dimensions, device model, and video duration when available.
- Thumbnail generation for browsing.
- Automatic grouping of media into trip records using capture dates, weekend windows, time gaps, and GPS clustering.
- A local database for files, metadata, locations, and trip records.
- A LAN-only web interface for browsing trips, reviewing media, editing trip titles, and merging or splitting trip groups.

The first version does not include:

- Public internet access.
- Automatic phone sync.
- Full mobile app support.
- Face recognition.
- Advanced video analysis.
- Fully automatic publishing of final travel journals.

## Recommended Architecture

Use a file-based media library plus a small database and web application.

The media files remain on disk as the source of truth. The database stores extracted metadata, generated thumbnails, detected trip groups, user edits, and later AI-generated journal drafts. This keeps the system simple, recoverable, and easy to migrate.

Recommended stack:

- Backend: Python with FastAPI.
- Database: SQLite for the first version.
- Media tools: ExifTool for metadata, FFmpeg for video metadata and thumbnails.
- Frontend: React or a simple server-rendered UI, depending on implementation speed.
- Deployment: Docker Compose on the Ubuntu laptop.

SQLite is enough for a family archive in the first version. PostgreSQL can be introduced later if the system grows or if other services need shared data.

## Storage Layout

Use a clear directory structure on the server:

```text
family-album/
  incoming/
  library/
    originals/
    thumbnails/
    derivatives/
  data/
    album.sqlite
    geocode-cache.sqlite
  exports/
    journals/
```

`incoming/` is where the family copies new photos and videos.

`library/originals/` stores imported files after the scanner registers them. Files should be arranged by capture year and month, for example `library/originals/2026/06/`.

`library/thumbnails/` stores generated preview images.

`exports/journals/` will later store Markdown or HTML travel journals.

## Data Model

Core entities:

- `MediaFile`: one photo or video, with path, hash, file type, size, dimensions, capture time, GPS, device model, and scan status.
- `LocationPoint`: GPS latitude and longitude extracted from media.
- `Place`: a human-readable place derived from GPS lookup or manual naming.
- `Trip`: one detected outing, with title, date range, primary place, status, and confidence score.
- `TripMedia`: relationship between trips and media, including ordering and featured status.
- `UserEdit`: audit trail for manual corrections such as merging trips, splitting trips, or renaming places.

The system should preserve original metadata and record derived values separately so rescanning or improving algorithms does not destroy user edits.

## Import Flow

1. User copies files into `incoming/`.
2. Scanner detects supported media files.
3. Scanner calculates a content hash to avoid duplicates.
4. Scanner extracts metadata and stores it in the database.
5. Scanner moves or copies registered files into `library/originals/`.
6. Thumbnail worker creates previews.
7. Trip grouping worker assigns new files to existing or new trip records.
8. Web UI shows new or changed trip records for review.

By default, original files should not be deleted from `incoming/` until the import succeeds. The implementation can move files after success or keep a quarantine folder for failed imports.

## Trip Detection Rules

The first grouping algorithm should be explainable rather than clever.

Inputs:

- Capture date and time.
- Weekend or holiday-like time windows.
- GPS coordinates when available.
- Time gaps between shots.
- Distance between GPS points.

Initial heuristic:

- Sort media by capture time.
- Group media taken within the same weekend window.
- Split groups when time gaps are large and GPS locations are far apart.
- Merge groups when they are close in time and location.
- Mark trips with missing GPS as lower confidence.

Each trip gets a confidence value. Low-confidence trips should be easy to review manually in the UI.

Manual edits are part of the product, not an exception. Users must be able to merge two trips, split one trip, rename a trip, change the primary place, and mark featured photos.

## Location Handling

The first version should store raw GPS coordinates and use a cache for place names.

Reverse geocoding can start with one of these approaches:

- Manual place naming only.
- OpenStreetMap Nominatim with caching and rate limiting.
- A later paid map API if higher accuracy is needed.

The system should work even when reverse geocoding is unavailable. In that case, it can show coordinates, a map point if map tiles are available, or a manually entered place name.

## Web Interface

The first web interface should be practical and focused.

Main views:

- Trip list: date, title, place, thumbnail, media count, and confidence status.
- Trip detail: timeline, map area, photo/video grid, metadata summary, and edit controls.
- Import review: recently imported files and trips that need attention.
- Settings: library paths, scanner schedule, and location lookup configuration.

Important actions:

- Rename trip.
- Merge trips.
- Split trip by selected media.
- Mark featured media.
- Edit place name.
- Trigger rescan.

The UI should be optimized for repeated family use rather than a marketing-style landing page.

## AI Travel Journal Extension

AI-generated travel journals should come after reliable trip grouping.

Inputs for journal generation:

- Trip date and duration.
- Place names and rough route.
- Featured photos and selected video stills.
- Timeline of moments.
- Optional user notes.

Output:

- Markdown draft stored in `exports/journals/`.
- Editable title, summary, and sections.
- References to selected photos and videos.

The AI should generate drafts, not final truth. The family should be able to edit names, memories, tone, and details before exporting or sharing.

## Deployment

Run the system on the Ubuntu laptop with Docker Compose.

Services:

- Web/backend application.
- Background worker for scanning and thumbnails.
- Optional reverse geocoding cache.

First access mode:

- LAN only.
- URL similar to `http://server-ip:port`.
- No public port forwarding.

Later external access options:

- Tailscale or WireGuard VPN.
- Cloudflare Tunnel.
- Domain plus HTTPS reverse proxy.

External access should be treated as a separate project after local use is stable.

## Error Handling

The scanner should handle imperfect media libraries gracefully.

Expected cases:

- Duplicate files.
- Missing capture time.
- Missing GPS.
- Unsupported media formats.
- Corrupt files.
- Failed thumbnail generation.
- Reverse geocoding errors.

The database should record scan status and error messages. Failed files should appear in an import review screen instead of silently disappearing.

## Testing Strategy

Use focused tests around the highest-risk behavior:

- Metadata parsing with sample photo and video files.
- Duplicate detection.
- Trip grouping from synthetic timelines and GPS coordinates.
- Manual merge and split behavior.
- Import idempotency.
- API endpoints for trip list and trip detail.

Manual verification should include copying a small real photo set into `incoming/`, running the scanner, and confirming that generated trips match expectations.

## Milestones

1. Repository scaffold and Docker Compose baseline.
2. Media scanner with metadata extraction and duplicate detection.
3. Thumbnail generation.
4. SQLite schema and trip grouping worker.
5. Basic LAN web UI for trip list and trip detail.
6. Manual correction actions for merge, split, rename, and featured media.
7. Optional location lookup cache.
8. AI travel journal draft generation.

## First Implementation Defaults

- Use a simple server-rendered interface first, unless the implementation plan finds a strong reason to use React.
- Copy imported files into `library/originals/` after successful registration and leave the source files in `incoming/` until the user manually clears them.
- Start with manual place naming and raw GPS display. Add OpenStreetMap Nominatim with caching after the basic trip grouping flow works.
- Support configurable library paths from the beginning so an external disk can be mounted without changing application code.
