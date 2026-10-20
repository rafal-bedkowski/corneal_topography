"""Duplicate detection on accepted thickness values (spec 4.8)."""

from collections import defaultdict
from collections.abc import Sequence
from itertools import combinations

from app.constants import LABELS, SPLITS
from app.models import ExamRecord
from ingest.indicators import accepted_values

MIN_SHARED_VALUES = 4
MIN_OVERLAP = 0.6


def mark_duplicates(exams: Sequence[ExamRecord]) -> None:
    """Fill `possible_duplicate_of` and the statistics exclusion fields in place."""
    thickness = {exam.exam_id: set(accepted_values(exam.maps, "ct_a")) for exam in exams}
    candidates = [exam for exam in exams if len(thickness[exam.exam_id]) >= MIN_SHARED_VALUES]

    parent = {exam.exam_id: exam.exam_id for exam in candidates}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for first, second in combinations(candidates, 2):
        if _is_duplicate(first, second, thickness):
            parent[find(first.exam_id)] = find(second.exam_id)

    groups: dict[str, list[ExamRecord]] = defaultdict(list)
    for exam in candidates:
        groups[find(exam.exam_id)].append(exam)

    for members in groups.values():
        if len(members) < 2:
            continue
        for member in members:
            member.possible_duplicate_of = sorted(
                other.exam_id for other in members if other is not member
            )
        _apply_exclusion(members)


def _is_duplicate(first: ExamRecord, second: ExamRecord, thickness: dict[str, set[float]]) -> bool:
    if "unknown" not in (first.laterality, second.laterality) and (
        first.laterality != second.laterality
    ):
        return False
    one, two = thickness[first.exam_id], thickness[second.exam_id]
    shared = len(one & two)
    return shared >= MIN_SHARED_VALUES and shared / len(one | two) >= MIN_OVERLAP


def _apply_exclusion(members: list[ExamRecord]) -> None:
    if len({member.label for member in members}) > 1:
        for member in members:
            member.stats_excluded = True
            member.stats_exclusion_reason = "duplicate_conflicting_labels"
        return
    keeper = min(
        members, key=lambda exam: (SPLITS.index(exam.split), LABELS.index(exam.label), exam.case)
    )
    for member in members:
        if member is not keeper:
            member.stats_excluded = True
            member.stats_exclusion_reason = "duplicate"
