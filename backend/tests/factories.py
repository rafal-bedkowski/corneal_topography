"""Builders for synthetic exam records used across the tests."""

from app.constants import MAP_SPECS, Label, Laterality, MapType, Split
from app.models import ExamRecord, ExtractedValue, Indicators, MapRecord, make_exam_id


def value(
    text: str,
    number: float | None = None,
    status: str = "accepted",
    confidence: float = 1.0,
    x: float = 0.5,
    y: float = 0.5,
) -> ExtractedValue:
    return ExtractedValue.model_validate(
        {
            "text": text,
            "value": number,
            "confidence": confidence,
            "x": x,
            "y": y,
            "status": status,
        }
    )


def accepted(*numbers: float) -> list[ExtractedValue]:
    return [value(str(number), number) for number in numbers]


def make_maps(
    thickness: list[float] | None = None,
    curvature: list[float] | None = None,
    extra: dict[MapType, list[ExtractedValue]] | None = None,
) -> dict[MapType, MapRecord]:
    values: dict[MapType, list[ExtractedValue]] = {spec.map_type: [] for spec in MAP_SPECS}
    values["ct_a"] = accepted(*(thickness or []))
    values["sag_a"] = accepted(*(curvature or []))
    values.update(extra or {})
    return {
        spec.map_type: MapRecord(file=f"x/{spec.file_suffix}.jpg", values=values[spec.map_type])
        for spec in MAP_SPECS
    }


def make_exam(
    split: Split = "train_validation",
    label: Label = "normal",
    case: int = 1,
    laterality: Laterality = "OD",
    thickness: list[float] | None = None,
    curvature: list[float] | None = None,
    indicators: Indicators | None = None,
) -> ExamRecord:
    return ExamRecord(
        exam_id=make_exam_id(split, label, case),
        split=split,
        label=label,
        case=case,
        laterality=laterality,
        maps=make_maps(thickness, curvature),
        indicators=indicators or Indicators(),
    )
