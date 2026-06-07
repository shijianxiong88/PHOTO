# 家庭出游相册 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建第一版家庭出游相册系统，可以在 Ubuntu 家庭服务器上导入照片/视频、提取元数据、自动归并出游记录，并通过局域网网页查看。

**Architecture:** 使用 Python + FastAPI + SQLite + Jinja2 服务端渲染。媒体原文件保存在磁盘，数据库保存元数据、缩略图路径、出游记录和用户修正。扫描、聚合、Web 浏览先做成同一个应用内的清晰模块，后续再拆后台任务。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Jinja2, pytest, ExifTool, FFmpeg, Docker Compose, SQLite.

---

## 文件结构

- Create: `pyproject.toml` - Python 项目依赖、测试配置、格式化配置。
- Create: `README.md` - 本地运行、Docker 运行、目录说明。
- Create: `docker-compose.yml` - Ubuntu 家庭服务器部署入口。
- Create: `Dockerfile` - 应用容器镜像。
- Create: `.env.example` - 媒体库路径和数据库路径示例。
- Create: `app/main.py` - FastAPI 应用入口、路由注册、静态文件挂载。
- Create: `app/config.py` - 环境变量配置和默认路径。
- Create: `app/db.py` - SQLite engine、session、初始化入口。
- Create: `app/models.py` - SQLAlchemy 数据模型。
- Create: `app/schemas.py` - 内部数据结构和 API 表达对象。
- Create: `app/media/hash.py` - 文件哈希和重复识别基础函数。
- Create: `app/media/metadata.py` - ExifTool/FFprobe 元数据提取适配层。
- Create: `app/media/importer.py` - 扫描 `incoming/`、登记媒体、复制到 `library/originals/`。
- Create: `app/media/thumbnails.py` - 调用 FFmpeg 生成缩略图。
- Create: `app/trips/grouping.py` - 按时间窗口、间隔、GPS 距离生成出游记录。
- Create: `app/trips/service.py` - 出游查询、重命名、合并、拆分、精选媒体操作。
- Create: `app/web/routes.py` - Web 页面路由和表单动作。
- Create: `app/templates/base.html` - 基础布局。
- Create: `app/templates/trips.html` - 出游列表。
- Create: `app/templates/trip_detail.html` - 出游详情。
- Create: `app/templates/import_review.html` - 导入检查页面。
- Create: `app/static/styles.css` - 朴素可用的局域网页面样式。
- Create: `tests/conftest.py` - 测试数据库和临时媒体目录夹具。
- Create: `tests/test_hash.py` - 哈希与重复检测测试。
- Create: `tests/test_grouping.py` - 出游聚合算法测试。
- Create: `tests/test_importer.py` - 导入幂等性和文件复制测试。
- Create: `tests/test_trip_service.py` - 合并、拆分、重命名、精选媒体测试。
- Create: `tests/test_web.py` - Web 路由冒烟测试。

## Task 1: 项目骨架和配置

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 写配置测试**

Create `tests/test_config.py`:

```python
from pathlib import Path

from app.config import Settings


def test_settings_derive_library_paths(tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path)

    assert settings.incoming_dir == tmp_path / "incoming"
    assert settings.originals_dir == tmp_path / "library" / "originals"
    assert settings.thumbnails_dir == tmp_path / "library" / "thumbnails"
    assert settings.database_url == f"sqlite:///{tmp_path / 'data' / 'album.sqlite'}"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_config.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app'` or `ImportError` because app files do not exist yet.

- [ ] **Step 3: 创建项目依赖配置**

Create `pyproject.toml`:

```toml
[project]
name = "family-trip-album"
version = "0.1.0"
description = "家庭出游照片和视频整理系统"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "jinja2>=3.1.4",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0.32",
  "uvicorn[standard]>=0.30.0",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.27.0",
  "pytest>=8.3.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 4: 创建配置模块**

Create `app/__init__.py`:

```python
__all__ = []
```

Create `app/config.py`:

```python
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    media_root: Path = Path(os.getenv("MEDIA_ROOT", "./family-album")).resolve()
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    @property
    def incoming_dir(self) -> Path:
        return self.media_root / "incoming"

    @property
    def originals_dir(self) -> Path:
        return self.media_root / "library" / "originals"

    @property
    def thumbnails_dir(self) -> Path:
        return self.media_root / "library" / "thumbnails"

    @property
    def derivatives_dir(self) -> Path:
        return self.media_root / "library" / "derivatives"

    @property
    def data_dir(self) -> Path:
        return self.media_root / "data"

    @property
    def exports_dir(self) -> Path:
        return self.media_root / "exports" / "journals"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'album.sqlite'}"

    def ensure_directories(self) -> None:
        for path in (
            self.incoming_dir,
            self.originals_dir,
            self.thumbnails_dir,
            self.derivatives_dir,
            self.data_dir,
            self.exports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
```

Create `.env.example`:

```text
MEDIA_ROOT=/srv/family-album
APP_HOST=0.0.0.0
APP_PORT=8000
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_config.py -v`

Expected: PASS, one test passes.

- [ ] **Step 6: 添加 README**

Create `README.md`:

```markdown
# 家庭出游相册

这是一个运行在 Ubuntu 家庭服务器上的照片和视频整理系统。

第一版目标：

- 手动把手机照片和视频复制到 `incoming/`
- 扫描媒体文件并提取元数据
- 自动归并成一次次出游记录
- 在家庭局域网通过网页查看

默认目录：

```text
family-album/
  incoming/
  library/originals/
  library/thumbnails/
  data/album.sqlite
  exports/journals/
```

本地开发：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```
```

- [ ] **Step 7: 提交**

```bash
git add pyproject.toml README.md .env.example app/__init__.py app/config.py tests/test_config.py
git commit -m "chore: scaffold project configuration"
```

## Task 2: 数据库模型和初始化

**Files:**
- Create: `app/db.py`
- Create: `app/models.py`
- Modify: `app/config.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: 写数据库模型测试**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_models.py -v`

Expected: FAIL with import errors for `app.db` and `app.models`.

- [ ] **Step 3: 实现数据库入口**

Create `app/db.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_database(session_factory: sessionmaker[Session]) -> None:
    Base.metadata.create_all(session_factory.kw["bind"])


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- [ ] **Step 4: 实现数据模型**

Create `app/models.py`:

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

- [ ] **Step 5: 运行模型测试**

Run: `pytest tests/test_models.py -v`

Expected: PASS, model persistence works.

- [ ] **Step 6: 提交**

```bash
git add app/db.py app/models.py tests/test_models.py
git commit -m "feat: add database models"
```

## Task 3: 媒体哈希、元数据提取和导入

**Files:**
- Create: `app/media/__init__.py`
- Create: `app/media/hash.py`
- Create: `app/media/metadata.py`
- Create: `app/media/importer.py`
- Test: `tests/test_hash.py`
- Test: `tests/test_importer.py`

- [ ] **Step 1: 写哈希测试**

Create `tests/test_hash.py`:

```python
from pathlib import Path

from app.media.hash import sha256_file


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"same bytes")

    assert sha256_file(file_path) == sha256_file(file_path)
    assert sha256_file(file_path).startswith("15")
```

- [ ] **Step 2: 写导入测试**

Create `tests/test_importer.py`:

```python
from pathlib import Path

from app.config import Settings
from app.db import create_session_factory, init_database
from app.media.importer import import_incoming
from app.models import MediaFile


def test_import_incoming_copies_file_and_skips_duplicate(tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path)
    settings.ensure_directories()
    source = settings.incoming_dir / "IMG_0001.jpg"
    source.write_bytes(b"fake image bytes")

    session_factory = create_session_factory(settings.database_url)
    init_database(session_factory)

    first_result = import_incoming(settings, session_factory)
    second_result = import_incoming(settings, session_factory)

    assert first_result.imported_count == 1
    assert second_result.imported_count == 0
    with session_factory() as session:
        media = session.query(MediaFile).one()
        assert media.media_type == "photo"
        assert Path(media.original_path).exists()
        assert media.scan_status == "ready"
```

- [ ] **Step 3: 运行测试确认失败**

Run: `pytest tests/test_hash.py tests/test_importer.py -v`

Expected: FAIL because media modules do not exist.

- [ ] **Step 4: 实现哈希函数**

Create `app/media/__init__.py`:

```python
__all__ = []
```

Create `app/media/hash.py`:

```python
from hashlib import sha256
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 5: 实现元数据适配层**

Create `app/media/metadata.py`:

```python
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
```

- [ ] **Step 6: 实现导入流程**

Create `app/media/importer.py`:

```python
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
```

- [ ] **Step 7: 运行导入测试**

Run: `pytest tests/test_hash.py tests/test_importer.py -v`

Expected: PASS, hash and import behavior work for a fake photo file.

- [ ] **Step 8: 提交**

```bash
git add app/media tests/test_hash.py tests/test_importer.py
git commit -m "feat: import incoming media files"
```

## Task 4: 出游聚合算法

**Files:**
- Create: `app/trips/__init__.py`
- Create: `app/trips/grouping.py`
- Test: `tests/test_grouping.py`

- [ ] **Step 1: 写聚合测试**

Create `tests/test_grouping.py`:

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_grouping.py -v`

Expected: FAIL because `app.trips.grouping` does not exist.

- [ ] **Step 3: 实现聚合算法**

Create `app/trips/__init__.py`:

```python
__all__ = []
```

Create `app/trips/grouping.py`:

```python
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
```

- [ ] **Step 4: 运行聚合测试**

Run: `pytest tests/test_grouping.py -v`

Expected: PASS, grouping splits distant outings and handles missing GPS.

- [ ] **Step 5: 提交**

```bash
git add app/trips tests/test_grouping.py
git commit -m "feat: group media into trips"
```

## Task 5: 出游服务和人工修正操作

**Files:**
- Create: `app/trips/service.py`
- Test: `tests/test_trip_service.py`

- [ ] **Step 1: 写服务测试**

Create `tests/test_trip_service.py`:

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_trip_service.py -v`

Expected: FAIL because `app.trips.service` does not exist.

- [ ] **Step 3: 实现出游服务**

Create `app/trips/service.py`:

```python
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
```

- [ ] **Step 4: 运行服务测试**

Run: `pytest tests/test_trip_service.py -v`

Expected: PASS, rename and featured operations persist.

- [ ] **Step 5: 提交**

```bash
git add app/trips/service.py tests/test_trip_service.py
git commit -m "feat: add trip editing service"
```

## Task 6: FastAPI Web 页面

**Files:**
- Create: `app/main.py`
- Create: `app/web/__init__.py`
- Create: `app/web/routes.py`
- Create: `app/templates/base.html`
- Create: `app/templates/trips.html`
- Create: `app/templates/trip_detail.html`
- Create: `app/templates/import_review.html`
- Create: `app/static/styles.css`
- Test: `tests/test_web.py`

- [ ] **Step 1: 写 Web 冒烟测试**

Create `tests/test_web.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_trip_list_page_loads() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "出游记录" in response.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_web.py -v`

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: 创建 FastAPI 应用**

Create `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="家庭出游相册")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(router)
    return app


app = create_app()
```

Create `app/web/__init__.py`:

```python
__all__ = []
```

Create `app/web/routes.py`:

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def trip_list(request: Request):
    trips = []
    return templates.TemplateResponse("trips.html", {"request": request, "trips": trips})


@router.get("/imports")
def import_review(request: Request):
    return templates.TemplateResponse("import_review.html", {"request": request, "files": []})
```

- [ ] **Step 4: 创建模板和样式**

Create `app/templates/base.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}家庭出游相册{% endblock %}</title>
    <link rel="stylesheet" href="/static/styles.css">
  </head>
  <body>
    <header class="topbar">
      <a href="/" class="brand">家庭出游相册</a>
      <nav>
        <a href="/">出游记录</a>
        <a href="/imports">导入检查</a>
      </nav>
    </header>
    <main class="page">
      {% block content %}{% endblock %}
    </main>
  </body>
</html>
```

Create `app/templates/trips.html`:

```html
{% extends "base.html" %}
{% block title %}出游记录{% endblock %}
{% block content %}
<section class="section-header">
  <h1>出游记录</h1>
  <p>按周末、时间和地点自动整理出的家庭出游。</p>
</section>

{% if trips %}
  <div class="trip-list">
    {% for trip in trips %}
      <article class="trip-card">
        <h2>{{ trip.title }}</h2>
        <p>{{ trip.start_at }} - {{ trip.end_at }}</p>
      </article>
    {% endfor %}
  </div>
{% else %}
  <section class="empty-state">
    <h2>还没有出游记录</h2>
    <p>把照片或视频复制到 incoming 文件夹后，运行扫描任务即可生成记录。</p>
  </section>
{% endif %}
{% endblock %}
```

Create `app/templates/trip_detail.html`:

```html
{% extends "base.html" %}
{% block title %}出游详情{% endblock %}
{% block content %}
<section class="section-header">
  <h1>{{ trip.title }}</h1>
</section>
{% endblock %}
```

Create `app/templates/import_review.html`:

```html
{% extends "base.html" %}
{% block title %}导入检查{% endblock %}
{% block content %}
<section class="section-header">
  <h1>导入检查</h1>
  <p>查看最近导入、失败或需要人工确认的媒体文件。</p>
</section>
{% endblock %}
```

Create `app/static/styles.css`:

```css
:root {
  color-scheme: light;
  --bg: #f7f7f4;
  --text: #202124;
  --muted: #666b70;
  --line: #d9ddd7;
  --surface: #ffffff;
  --accent: #2f6f6d;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid var(--line);
  background: var(--surface);
}

.brand {
  color: var(--text);
  font-weight: 700;
  text-decoration: none;
}

nav {
  display: flex;
  gap: 16px;
}

nav a {
  color: var(--accent);
  text-decoration: none;
}

.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px 20px;
}

.section-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.section-header p,
.empty-state p {
  color: var(--muted);
}

.empty-state {
  margin-top: 24px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}
```

- [ ] **Step 5: 运行 Web 测试**

Run: `pytest tests/test_web.py -v`

Expected: PASS, homepage returns HTML containing `出游记录`.

- [ ] **Step 6: 提交**

```bash
git add app/main.py app/web app/templates app/static tests/test_web.py
git commit -m "feat: add basic web interface"
```

## Task 7: Docker Compose 和手动验收

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: 创建 Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg exiftool \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY app /app/app

RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建 Docker Compose**

Create `docker-compose.yml`:

```yaml
services:
  family-album:
    build: .
    ports:
      - "8000:8000"
    environment:
      MEDIA_ROOT: /srv/family-album
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
    volumes:
      - ./family-album:/srv/family-album
```

- [ ] **Step 3: 更新 README 运行说明**

Append to `README.md`:

```markdown

## Docker 运行

```bash
docker compose up --build
```

浏览器访问：

```text
http://localhost:8000
```

在 Ubuntu 家庭服务器上，把 `./family-album` 换成外接硬盘或服务器上的真实目录即可。
```

- [ ] **Step 4: 运行全部测试**

Run: `pytest -v`

Expected: PASS, all tests pass.

- [ ] **Step 5: 构建容器**

Run: `docker compose build`

Expected: Build completes successfully and installs Python dependencies plus FFmpeg/ExifTool.

- [ ] **Step 6: 启动服务**

Run: `docker compose up`

Expected: Uvicorn starts and logs `Application startup complete`.

- [ ] **Step 7: 手动浏览页面**

Open: `http://localhost:8000`

Expected:

- Page title shows `出游记录`.
- Empty state explains that imported files should be copied to `incoming`.
- Navigation includes `出游记录` and `导入检查`.

- [ ] **Step 8: 提交**

```bash
git add Dockerfile docker-compose.yml README.md
git commit -m "chore: add docker deployment"
```

## Task 8: 第一版完成检查

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 运行全量测试**

Run: `pytest -v`

Expected: PASS, no failures.

- [ ] **Step 2: 检查 git 状态**

Run: `git status --short`

Expected: no output after all intended files are committed.

- [ ] **Step 3: 在 README 添加第一版验收清单**

Append to `README.md`:

```markdown

## 第一版验收清单

- [ ] 可以启动 Web 服务
- [ ] 首页可以在局域网浏览器访问
- [ ] 可以把照片或视频放入 `incoming/`
- [ ] 扫描流程可以登记媒体文件并跳过重复文件
- [ ] 出游聚合算法可以把相近时间的媒体归为一组
- [ ] 可以通过服务函数重命名出游记录和标记精选媒体
```

- [ ] **Step 4: 提交验收文档**

```bash
git add README.md
git commit -m "docs: add mvp acceptance checklist"
```

## 自查结果

- 设计文档中的第一版范围均已覆盖：手动导入、扫描、元数据基础结构、缩略图位置、出游聚合、数据库、局域网 Web 页面、人工修正服务。
- AI 游记、外网访问、自动手机同步、人脸识别在设计中明确为后续阶段，本计划只预留目录和数据边界。
- 计划没有使用占位任务或未定义函数名。每个新增模块都在对应任务中定义，并有可运行测试或手动验收命令。
