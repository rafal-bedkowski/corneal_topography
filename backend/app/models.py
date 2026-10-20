"""Domain models stored in the exam index (written by `ingest`, read by `app`)."""

from pydantic import BaseModel, Field

from app.constants import (
    INDEX_VERSION,
    ExclusionReason,
    Label,
    Laterality,
    MapType,
    Split,
    ValueStatus,
)


class ExtractedValue(BaseModel):
    text: str
    value: float | None
    confidence: float = Field(ge=0, le=1)
    x: float
    y: float
    status: ValueStatus


class MapRecord(BaseModel):
    file: str
    values: list[ExtractedValue]


class Indicators(BaseModel):
    min_thickness_um: float | None = None
    max_curvature_a_d: float | None = None
    min_curvature_a_d: float | None = None
    curvature_spread_a_d: float | None = None
    max_elevation_a_um: float | None = None
    max_elevation_p_um: float | None = None


class ExamRecord(BaseModel):
    exam_id: str
    split: Split
    label: Label
    case: int
    laterality: Laterality
    maps: dict[MapType, MapRecord]
    indicators: Indicators
    possible_duplicate_of: list[str] = Field(default_factory=list)
    stats_excluded: bool = False
    stats_exclusion_reason: ExclusionReason | None = None


class ExamIndex(BaseModel):
    version: int = INDEX_VERSION
    generated_at: str
    exams: list[ExamRecord]


def make_exam_id(split: Split, label: Label, case: int) -> str:
    return f"{split}/{label}/{case}"
