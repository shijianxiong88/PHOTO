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
