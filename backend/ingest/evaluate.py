"""Scoring of an exam index against the hand-read gold sample (`input_data/gold`)."""

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT, Settings
from app.models import ExamIndex, ExamRecord

GOLD_PATH = REPO_ROOT / "input_data" / "gold" / "gold_sample.json"
INDICATOR_FIELDS = (
    "min_thickness_um",
    "max_curvature_a_d",
    "min_curvature_a_d",
    "max_elevation_a_um",
    "max_elevation_p_um",
)
SETS = ("tuning", "holdout", "all")


@dataclass
class Score:
    correct: int = 0
    scored: int = 0
    by_field: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def ratio(self) -> float:
        return self.correct / self.scored if self.scored else 0.0

    def add(self, name: str, ok: bool) -> None:
        correct, scored = self.by_field.get(name, (0, 0))
        self.by_field[name] = (correct + ok, scored + 1)
        self.correct += ok
        self.scored += 1


def load_gold(path: Path = GOLD_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    exams: list[dict[str, Any]] = data["exams"]
    return exams


def select(gold: Sequence[dict[str, Any]], which: str) -> list[dict[str, Any]]:
    return [item for item in gold if which == "all" or item["set"] == which]


def score(index: ExamIndex, gold: Sequence[dict[str, Any]]) -> Score:
    exams: dict[str, ExamRecord] = {exam.exam_id: exam for exam in index.exams}
    result = Score()
    for item in gold:
        exam = exams[item["exam_id"]]
        result.add("laterality", exam.laterality == item["laterality"])
        for name in INDICATOR_FIELDS:
            accepted = item["indicators"][name]
            if accepted is None:
                continue
            got = getattr(exam.indicators, name)
            result.add(name, got is not None and any(abs(got - want) < 1e-9 for want in accepted))
    return result


def format_score(label: str, value: Score) -> str:
    fields = ", ".join(f"{name} {ok}/{total}" for name, (ok, total) in value.by_field.items())
    return f"{label}: {value.correct}/{value.scored} = {value.ratio:.1%}  ({fields})"


def run(argv: Sequence[str] | None = None) -> int:
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(
        prog="python -m ingest.evaluate",
        description="Score the exam index against the gold sample.",
    )
    parser.add_argument("--index", type=Path, default=settings.index_path)
    parser.add_argument("--set", choices=SETS, default="tuning", dest="which")
    args = parser.parse_args(argv)
    index = ExamIndex.model_validate_json(args.index.read_text(encoding="utf-8"))
    gold = select(load_gold(), args.which)
    print(format_score(args.which, score(index, gold)))
    return 0


if __name__ == "__main__":
    sys.exit(run())
