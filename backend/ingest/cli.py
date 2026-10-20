import argparse
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from app.config import Settings
from app.constants import VALUE_STATUSES
from app.models import ExamIndex
from ingest.builder import BuildResult, build_index
from ingest.ocr import OcrUnavailableError, Recogniser, ensure_macos, recognise_images
from ingest.rules import RawToken


def write_index_atomically(index: ExamIndex, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(index.model_dump_json())
        os.replace(temp_name, target)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def summarise(result: BuildResult) -> str:
    exams = result.index.exams
    lines = [f"Exams indexed: {len(exams)}"]
    lines.append(f"Exams skipped: {len(result.skipped)}")
    lines.extend(f"  {item.path}: {item.reason}" for item in result.skipped)
    counts = ", ".join(
        f"{status}={result.value_statuses.get(status, 0)}" for status in VALUE_STATUSES
    )
    lines.append(f"Extracted values: {counts}")
    lines.append(f"Exams without laterality: {sum(exam.laterality == 'unknown' for exam in exams)}")

    groups = {
        tuple(sorted([exam.exam_id, *exam.possible_duplicate_of]))
        for exam in exams
        if exam.possible_duplicate_of
    }
    reasons = Counter(exam.stats_exclusion_reason for exam in exams if exam.stats_excluded)
    lines.append(
        f"Duplicate groups: {len(groups)} "
        f"(excluded from statistics: duplicate={reasons['duplicate']}, "
        f"duplicate_conflicting_labels={reasons['duplicate_conflicting_labels']})"
    )
    lines.extend("  " + " = ".join(group) for group in sorted(groups))
    return "\n".join(lines)


def recognise_with_progress(images: Sequence[Path]) -> dict[Path, list[list[RawToken]]]:
    return recognise_images(
        images, progress=lambda message: print(message, file=sys.stderr, flush=True)
    )


def run(argv: Sequence[str] | None = None, recognise: Recogniser = recognise_with_progress) -> int:
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(
        prog="python -m ingest",
        description="Build the exam index (OCR of the map images). Runs on macOS only.",
    )
    parser.add_argument("--dataset-dir", type=Path, default=settings.dataset_dir)
    parser.add_argument("--output", type=Path, default=settings.index_path)
    args = parser.parse_args(argv)

    try:
        ensure_macos()
        if not args.dataset_dir.is_dir():
            raise OcrUnavailableError(f"Dataset directory not found: {args.dataset_dir}")
        result = build_index(args.dataset_dir, recognise)
    except OcrUnavailableError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    write_index_atomically(result.index, args.output)
    print(summarise(result))
    print(f"Index written to {args.output}")
    return 0
