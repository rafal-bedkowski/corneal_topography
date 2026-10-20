import re
from dataclasses import dataclass, field
from pathlib import Path

from app.constants import (
    LABEL_DIRS,
    LABEL_PREFIXES,
    LABELS,
    MAP_SPECS,
    SPLIT_DIRS,
    SPLITS,
    Label,
    MapType,
    Split,
)

CASE_DIR = re.compile(r"^case(\d+)$")


@dataclass(frozen=True)
class DiscoveredExam:
    split: Split
    label: Label
    case: int
    files: dict[MapType, str]  # path relative to the dataset directory


@dataclass(frozen=True)
class SkippedExam:
    path: str
    reason: str


@dataclass
class Discovery:
    exams: list[DiscoveredExam] = field(default_factory=list)
    skipped: list[SkippedExam] = field(default_factory=list)


def discover(dataset_dir: Path) -> Discovery:
    """Find exams under `<split dir>/<split dir>/<class dir>/case<N>`.

    Entries that do not look like case folders (e.g. `.DS_Store`) are ignored. A case folder
    without exactly the seven expected files is skipped and reported.
    """
    result = Discovery()
    for split in SPLITS:
        split_root = dataset_dir / SPLIT_DIRS[split] / SPLIT_DIRS[split]
        for label in LABELS:
            label_root = split_root / LABEL_DIRS[label]
            if not label_root.is_dir():
                continue
            for case_dir in sorted(label_root.iterdir(), key=lambda path: path.name):
                match = CASE_DIR.match(case_dir.name)
                if match is None or not case_dir.is_dir():
                    continue
                _add_case(result, dataset_dir, split, label, int(match.group(1)), case_dir)
    result.exams.sort(
        key=lambda exam: (SPLITS.index(exam.split), LABELS.index(exam.label), exam.case)
    )
    return result


def _add_case(
    result: Discovery, dataset_dir: Path, split: Split, label: Label, case: int, case_dir: Path
) -> None:
    expected = {
        spec.map_type: f"{LABEL_PREFIXES[label]}_{case}_{spec.file_suffix}.jpg"
        for spec in MAP_SPECS
    }
    present = {path.name for path in case_dir.iterdir() if path.name != ".DS_Store"}
    missing = sorted(set(expected.values()) - present)
    unexpected = sorted(present - set(expected.values()))
    relative = str(case_dir.relative_to(dataset_dir))
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        result.skipped.append(SkippedExam(relative, "; ".join(details)))
        return
    result.exams.append(
        DiscoveredExam(
            split=split,
            label=label,
            case=case,
            files={map_type: f"{relative}/{name}" for map_type, name in expected.items()},
        )
    )
