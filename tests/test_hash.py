from pathlib import Path

from app.media.hash import sha256_file


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"same bytes")

    assert sha256_file(file_path) == sha256_file(file_path)
    assert sha256_file(file_path) == (
        "58100dc8fc06562ce3e578231dc948e083520ee49c4b4ee5a5a28bb4b4003feb"
    )
