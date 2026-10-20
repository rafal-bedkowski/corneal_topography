"""AC1-AC8, AC24, AC27, AC28 against the real index."""

import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from app.config import Settings
from app.constants import MAP_SPECS
from app.models import ExamIndex, ExamRecord

REFERENCE_PAIRS = [
    ("independent_test/keratoconus/3", "independent_test/suspect/7"),
    ("independent_test/keratoconus/47", "independent_test/suspect/41"),
    ("independent_test/normal/25", "independent_test/suspect/39"),
    ("independent_test/normal/26", "independent_test/suspect/40"),
    ("train_validation/normal/125", "train_validation/suspect/75"),
    ("independent_test/suspect/4", "train_validation/suspect/109"),
    ("train_validation/keratoconus/78", "train_validation/keratoconus/84"),
    ("train_validation/keratoconus/79", "train_validation/keratoconus/85"),
    ("train_validation/normal/127", "train_validation/normal/42"),
    ("train_validation/normal/142", "train_validation/normal/94"),
    ("train_validation/normal/2", "train_validation/normal/53"),
    ("train_validation/suspect/115", "train_validation/suspect/116"),
]
INDICATORS = (
    "min_thickness_um",
    "max_curvature_a_d",
    "min_curvature_a_d",
    "max_elevation_a_um",
    "max_elevation_p_um",
)


def test_ac1_exam_counts(index: ExamIndex) -> None:
    assert len(index.exams) == 573
    assert Counter(e.label for e in index.exams) == {
        "normal": 200,
        "keratoconus": 200,
        "suspect": 173,
    }
    assert Counter(e.split for e in index.exams) == {
        "train_validation": 423,
        "independent_test": 150,
    }
    assert len({e.exam_id for e in index.exams}) == 573


def test_ac2_seven_maps_with_existing_files(index: ExamIndex, settings: Settings) -> None:
    expected = {spec.map_type for spec in MAP_SPECS}
    for exam in index.exams:
        assert set(exam.maps) == expected, exam.exam_id
        for record in exam.maps.values():
            assert (settings.dataset_dir / record.file).is_file(), record.file


def test_ac3_no_stray_entries(index: ExamIndex) -> None:
    assert all(".DS_Store" not in r.file for e in index.exams for r in e.maps.values())
    assert all(e.exam_id.count("/") == 2 for e in index.exams)


def test_ac6_perimeter_labels_are_never_accepted(index: ExamIndex) -> None:
    for exam in index.exams:
        for record in exam.maps.values():
            for value in record.values:
                if value.status != "accepted":
                    continue
                assert "°" not in value.text and not any(c.isalpha() for c in value.text), value
                assert ((value.x - 0.5) ** 2 + (value.y - 0.5) ** 2) ** 0.5 <= 0.42, value


def test_accepted_values_satisfy_the_spec_ranges(index: ExamIndex) -> None:
    ranges = {
        "sag_a": (30.0, 75.0),
        "sag_p": (-15.0, -3.0),
        "elv_a": (-300, 300),
        "elv_p": (-300, 300),
        "ec_a": (-300, 300),
        "ec_p": (-300, 300),
        "ct_a": (300, 900),
    }
    for exam in index.exams:
        for map_type, record in exam.maps.items():
            low, high = ranges[map_type]
            for value in record.values:
                if value.status == "accepted":
                    assert value.value is not None and low <= value.value <= high, (
                        exam.exam_id,
                        value,
                    )
                    assert 0.5 <= value.confidence <= 1.0, (exam.exam_id, value)


def _matches(got: float | None, accepted: list[float]) -> bool:
    return got is not None and any(abs(got - want) < 1e-9 for want in accepted)


def _gold_scores(exams: dict[str, ExamRecord], gold: list[dict[str, Any]]) -> tuple[int, int, int]:
    scored = correct = thickness_correct = 0
    for item in gold:
        exam = exams[item["exam_id"]]
        scored += 1
        correct += exam.laterality == item["laterality"]
        for key in INDICATORS:
            accepted = item["indicators"][key]
            if accepted is None:
                continue
            scored += 1
            ok = _matches(getattr(exam.indicators, key), accepted)
            correct += ok
            if key == "min_thickness_um":
                thickness_correct += ok
    return scored, correct, thickness_correct


@pytest.mark.parametrize("which", ["tuning", "holdout"])
def test_r8_gold_sample_accuracy(
    which: str, exams: dict[str, ExamRecord], gold: list[dict[str, Any]]
) -> None:
    selected = [item for item in gold if item["set"] == which]
    scored, correct, _ = _gold_scores(exams, selected)
    assert correct / scored >= 0.85, f"{which}: {correct}/{scored} = {correct / scored:.1%}"


def test_r8_gold_sample_thickness(exams: dict[str, ExamRecord], gold: list[dict[str, Any]]) -> None:
    _, _, thickness_correct = _gold_scores(exams, gold)
    assert thickness_correct >= 28, f"{thickness_correct}/{len(gold)}"


def test_r8_gold_sample_laterality(
    exams: dict[str, ExamRecord], gold: list[dict[str, Any]]
) -> None:
    assert all(exams[g["exam_id"]].laterality == g["laterality"] for g in gold)


def test_ac24_dataset_and_index_are_not_tracked(repo_root: Path, settings: Settings) -> None:
    for path in (settings.dataset_dir / "Independent Test Set", settings.index_path):
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)], cwd=repo_root, check=False
        )
        assert result.returncode == 0, f"{path} is not ignored by git"
    tracked = subprocess.run(
        ["git", "ls-files", "dataset/archive", "backend/data"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert tracked.stdout.strip() == ""


def test_ac27_reference_duplicate_pairs(exams: dict[str, ExamRecord]) -> None:
    found = [pair for pair in REFERENCE_PAIRS if pair[1] in exams[pair[0]].possible_duplicate_of]
    assert len(found) >= 10, f"only {len(found)} of 12 pairs flagged"


def test_ac27_flagged_groups_share_thickness_values(exams: dict[str, ExamRecord]) -> None:
    for exam in exams.values():
        mine = {
            v.value
            for v in exam.maps["ct_a"].values
            if v.status == "accepted" and v.value is not None
        }
        for other_id in exam.possible_duplicate_of:
            theirs = {
                v.value
                for v in exams[other_id].maps["ct_a"].values
                if v.status == "accepted" and v.value is not None
            }
            assert len(mine & theirs) >= 4, (exam.exam_id, other_id)
            assert exam.exam_id in exams[other_id].possible_duplicate_of


def _groups(exams: dict[str, ExamRecord]) -> list[list[ExamRecord]]:
    seen: set[str] = set()
    groups = []
    for exam in exams.values():
        if exam.possible_duplicate_of and exam.exam_id not in seen:
            stack, members = [exam.exam_id], []
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                members.append(exams[current])
                stack.extend(exams[current].possible_duplicate_of)
            groups.append(members)
    return groups


def test_ac28_exclusion_rules_hold_for_every_group(exams: dict[str, ExamRecord]) -> None:
    groups = _groups(exams)
    assert groups
    for members in groups:
        labels = {m.label for m in members}
        kept = [m for m in members if not m.stats_excluded]
        if len(labels) > 1:
            assert kept == [], [m.exam_id for m in members]
            assert {m.stats_exclusion_reason for m in members} == {"duplicate_conflicting_labels"}
        else:
            assert len(kept) == 1, [m.exam_id for m in members]
            expected = min(
                members,
                key=lambda e: (e.split != "train_validation", e.case),
            )
            assert kept[0] is expected
            assert {m.stats_exclusion_reason for m in members if m.stats_excluded} == {"duplicate"}


def test_non_duplicates_are_not_excluded(exams: dict[str, ExamRecord]) -> None:
    for exam in exams.values():
        if not exam.possible_duplicate_of:
            assert not exam.stats_excluded and exam.stats_exclusion_reason is None
