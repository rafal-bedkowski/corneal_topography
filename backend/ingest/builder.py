from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.constants import MAP_SPECS, MapType
from app.models import ExamIndex, ExamRecord, MapRecord, make_exam_id
from ingest.consensus import merge_passes
from ingest.discovery import DiscoveredExam, SkippedExam, discover
from ingest.duplicates import mark_duplicates
from ingest.engines import Recogniser
from ingest.indicators import compute_indicators, detect_laterality
from ingest.plausibility import refine
from ingest.rules import RawToken


@dataclass
class BuildResult:
    index: ExamIndex
    skipped: list[SkippedExam]
    value_statuses: Counter[str] = field(default_factory=Counter)


def build_index(dataset_dir: Path, recognise: Recogniser) -> BuildResult:
    discovery = discover(dataset_dir)
    images = [
        dataset_dir / relative for exam in discovery.exams for relative in exam.files.values()
    ]
    tokens = recognise(images)

    exams = [_build_exam(exam, dataset_dir, tokens) for exam in discovery.exams]
    mark_duplicates(exams)

    statuses: Counter[str] = Counter(
        value.status for exam in exams for record in exam.maps.values() for value in record.values
    )
    index = ExamIndex(generated_at=datetime.now(UTC).isoformat(timespec="seconds"), exams=exams)
    return BuildResult(index=index, skipped=discovery.skipped, value_statuses=statuses)


def _build_exam(
    exam: DiscoveredExam, dataset_dir: Path, tokens: dict[Path, list[list[RawToken]]]
) -> ExamRecord:
    maps: dict[MapType, MapRecord] = {}
    for spec in MAP_SPECS:
        relative = exam.files[spec.map_type]
        maps[spec.map_type] = MapRecord(
            file=relative,
            values=refine(
                merge_passes(tokens[dataset_dir / relative], spec.map_type), spec.map_type
            ),
        )
    return ExamRecord(
        exam_id=make_exam_id(exam.split, exam.label, exam.case),
        split=exam.split,
        label=exam.label,
        case=exam.case,
        laterality=detect_laterality(maps),
        maps=maps,
        indicators=compute_indicators(maps),
    )
