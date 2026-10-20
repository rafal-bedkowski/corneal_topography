import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from app.constants import INDEX_VERSION
from app.models import ExamIndex, ExamRecord

MISSING_INDEX_HINT = (
    "Exam index not available. Run the ingestion command (`python -m ingest` in the backend "
    "directory, macOS only) to build it."
)


class IndexUnavailableError(Exception):
    """The exam index is missing, unreadable or has an unsupported version."""


@dataclass(frozen=True)
class _Loaded:
    mtime_ns: int
    exams: tuple[ExamRecord, ...]
    by_id: dict[str, ExamRecord]


class IndexStore:
    """Serves the exam index from disk and reloads it when the file changes."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._loaded: _Loaded | None = None

    def exams(self) -> tuple[ExamRecord, ...]:
        return self._load().exams

    def get(self, exam_id: str) -> ExamRecord | None:
        return self._load().by_id.get(exam_id)

    def _load(self) -> _Loaded:
        try:
            mtime_ns = self._path.stat().st_mtime_ns
        except OSError as error:
            raise IndexUnavailableError(MISSING_INDEX_HINT) from error
        if self._loaded is not None and self._loaded.mtime_ns == mtime_ns:
            return self._loaded
        try:
            index = ExamIndex.model_validate(json.loads(self._path.read_text(encoding="utf-8")))
        except (OSError, ValueError, ValidationError) as error:
            raise IndexUnavailableError(
                f"Exam index at {self._path} is unreadable or invalid. Re-run the ingestion."
            ) from error
        if index.version != INDEX_VERSION:
            raise IndexUnavailableError(
                f"Exam index version {index.version} is not supported. Re-run the ingestion."
            )
        self._loaded = _Loaded(
            mtime_ns=mtime_ns,
            exams=tuple(index.exams),
            by_id={exam.exam_id: exam for exam in index.exams},
        )
        return self._loaded
