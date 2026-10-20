"""API response schemas."""

from pydantic import BaseModel, Field

from app.constants import ExclusionReason, Label, Laterality, MapType, Split
from app.models import ExtractedValue, Indicators


class HealthResponse(BaseModel):
    status: str
    exams: int


class ExamSummary(BaseModel):
    exam_id: str
    split: Split
    label: Label
    case: int
    laterality: Laterality
    min_thickness_um: float | None
    max_curvature_a_d: float | None
    possible_duplicate_of: list[str]
    stats_excluded: bool
    thumbnail_url: str | None


class ExamPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ExamSummary]


class MapDetail(BaseModel):
    title: str
    unit: str
    image_url: str
    values: list[ExtractedValue]


class ExamDetail(BaseModel):
    exam_id: str
    split: Split
    label: Label
    case: int
    laterality: Laterality
    maps: dict[MapType, MapDetail]
    indicators: Indicators
    possible_duplicate_of: list[str]
    stats_excluded: bool
    stats_exclusion_reason: ExclusionReason | None


class SummaryStats(BaseModel):
    n: int
    mean: float | None
    median: float | None
    std: float | None
    min: float | None
    max: float | None


class HistogramBin(BaseModel):
    from_: float = Field(alias="from")
    count: int


class Histogram(BaseModel):
    bin_width: int
    bins: list[HistogramBin]


class ExtractionCounts(BaseModel):
    accepted: int
    low_confidence: int
    out_of_range: int
    rejected: int


class ClassStats(BaseModel):
    label: Label
    exams: int
    excluded_duplicates: int
    laterality: dict[Laterality, int]
    indicators: dict[str, SummaryStats]
    histograms: dict[str, Histogram]
    extraction: ExtractionCounts


class StatsResponse(BaseModel):
    classes: list[ClassStats]
