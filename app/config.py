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
