from pathlib import Path

from app.config import Settings


def test_settings_derive_library_paths(tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path)

    assert settings.incoming_dir == tmp_path / "incoming"
    assert settings.originals_dir == tmp_path / "library" / "originals"
    assert settings.thumbnails_dir == tmp_path / "library" / "thumbnails"
    assert settings.database_url == f"sqlite:///{tmp_path / 'data' / 'album.sqlite'}"
