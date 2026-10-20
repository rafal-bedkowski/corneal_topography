import math
import statistics
from collections.abc import Sequence

from app.constants import LABELS, LATERALITIES, VALUE_STATUSES, Split
from app.models import ExamRecord
from app.schemas import (
    ClassStats,
    ExtractionCounts,
    Histogram,
    HistogramBin,
    StatsResponse,
    SummaryStats,
)

INDICATOR_FIELDS = (
    "min_thickness_um",
    "max_curvature_a_d",
    "min_curvature_a_d",
    "curvature_spread_a_d",
    "max_elevation_a_um",
    "max_elevation_p_um",
)
HISTOGRAM_FIELD = "min_thickness_um"
HISTOGRAM_BIN_WIDTH = 20


def compute_stats(exams: Sequence[ExamRecord], split: Split | None) -> StatsResponse:
    scoped = [exam for exam in exams if split is None or exam.split == split]
    classes = []
    for label in LABELS:
        of_class = [exam for exam in scoped if exam.label == label]
        included = [exam for exam in of_class if not exam.stats_excluded]
        classes.append(
            ClassStats(
                label=label,
                exams=len(included),
                excluded_duplicates=len(of_class) - len(included),
                laterality={
                    lat: sum(1 for exam in included if exam.laterality == lat)
                    for lat in LATERALITIES
                },
                indicators={
                    field: summarise(_indicator_values(included, field))
                    for field in INDICATOR_FIELDS
                },
                histograms={
                    HISTOGRAM_FIELD: histogram(
                        _indicator_values(included, HISTOGRAM_FIELD), HISTOGRAM_BIN_WIDTH
                    )
                },
                extraction=_extraction_counts(included),
            )
        )
    return StatsResponse(classes=classes)


def summarise(values: Sequence[float]) -> SummaryStats:
    if not values:
        return SummaryStats(n=0, mean=None, median=None, std=None, min=None, max=None)
    return SummaryStats(
        n=len(values),
        mean=statistics.fmean(values),
        median=statistics.median(values),
        std=statistics.stdev(values) if len(values) >= 2 else None,
        min=min(values),
        max=max(values),
    )


def histogram(values: Sequence[float], bin_width: int) -> Histogram:
    if not values:
        return Histogram(bin_width=bin_width, bins=[])
    first = math.floor(min(values) / bin_width) * bin_width
    last = math.floor(max(values) / bin_width) * bin_width
    counts = {start: 0 for start in range(first, last + bin_width, bin_width)}
    for value in values:
        counts[math.floor(value / bin_width) * bin_width] += 1
    return Histogram(
        bin_width=bin_width,
        bins=[
            HistogramBin.model_validate({"from": start, "count": count})
            for start, count in counts.items()
        ],
    )


def _indicator_values(exams: Sequence[ExamRecord], field: str) -> list[float]:
    values = (getattr(exam.indicators, field) for exam in exams)
    return [value for value in values if value is not None]


def _extraction_counts(exams: Sequence[ExamRecord]) -> ExtractionCounts:
    counts = dict.fromkeys(VALUE_STATUSES, 0)
    for exam in exams:
        for map_record in exam.maps.values():
            for value in map_record.values:
                counts[value.status] += 1
    return ExtractionCounts(**counts)
