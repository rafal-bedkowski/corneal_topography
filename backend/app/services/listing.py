from collections.abc import Iterable
from typing import Literal

from app.constants import LABELS, SPLITS, Label, Laterality, Split
from app.models import ExamRecord

SortKey = Literal["case", "min_thickness"]
SortOrder = Literal["asc", "desc"]


def filter_exams(
    exams: Iterable[ExamRecord],
    split: Split | None,
    label: Label | None,
    laterality: Laterality | None,
) -> list[ExamRecord]:
    return [
        exam
        for exam in exams
        if (split is None or exam.split == split)
        and (label is None or exam.label == label)
        and (laterality is None or exam.laterality == laterality)
    ]


def sort_exams(exams: list[ExamRecord], key: SortKey, order: SortOrder) -> list[ExamRecord]:
    reverse = order == "desc"
    if key == "case":
        return sorted(exams, key=_case_key, reverse=reverse)
    with_value = [exam for exam in exams if exam.indicators.min_thickness_um is not None]
    without_value = [exam for exam in exams if exam.indicators.min_thickness_um is None]
    with_value.sort(key=lambda exam: (_thickness(exam), _case_key(exam)), reverse=reverse)
    without_value.sort(key=_case_key)
    return with_value + without_value


def paginate[T](items: list[T], page: int, page_size: int) -> list[T]:
    start = (page - 1) * page_size
    return items[start : start + page_size]


def _case_key(exam: ExamRecord) -> tuple[int, int, int]:
    return (SPLITS.index(exam.split), LABELS.index(exam.label), exam.case)


def _thickness(exam: ExamRecord) -> float:
    value = exam.indicators.min_thickness_um
    assert value is not None
    return value
