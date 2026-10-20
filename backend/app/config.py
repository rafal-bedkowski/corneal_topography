import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

DEFAULT_DATASET_DIR = "dataset/archive"
DEFAULT_INDEX_PATH = "backend/data/exams.json"
DEFAULT_CORS_ORIGINS = "http://localhost:3000"


@dataclass(frozen=True)
class Settings:
    dataset_dir: Path
    index_path: Path
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env
        origins = source.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
        return cls(
            dataset_dir=_resolve(source.get("DATASET_DIR", DEFAULT_DATASET_DIR)),
            index_path=_resolve(source.get("EXAMS_INDEX_PATH", DEFAULT_INDEX_PATH)),
            cors_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
        )


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path
