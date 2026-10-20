"""Plausibility rules applied to the values of one map after the passes were merged.

- Thickness: the printed values form a column of boxes, increasing from the thinnest point
  downwards. A topmost reading that too few passes agree on is promoted when it fits the column.
- Curvature and elevation: a value that is far from all of its neighbours is an OCR misread.
"""

import math
import statistics
from collections.abc import Sequence

from app.constants import MapType
from app.models import ExtractedValue

COLUMN_WIDTH = 0.06  # horizontal spread of the thickness boxes, fraction of the image width
PROMOTION_MIN_GAP = 5.0  # µm between the promoted value and the next one down
PROMOTION_MAX_GAP = 150.0
NEIGHBOUR_RADIUS = 0.15  # fraction of the image size
MIN_NEIGHBOURS = 3
CURVATURE_JUMP = 12.0  # D
ELEVATION_JUMP = 100.0  # µm

_CURVATURE_MAPS: frozenset[MapType] = frozenset({"sag_a", "sag_p"})
_ELEVATION_MAPS: frozenset[MapType] = frozenset({"elv_a", "elv_p", "ec_a", "ec_p"})


def refine(values: Sequence[ExtractedValue], map_type: MapType) -> list[ExtractedValue]:
    if map_type == "ct_a":
        return promote_top_thickness(values)
    if map_type in _CURVATURE_MAPS:
        return flag_outliers(values, CURVATURE_JUMP)
    if map_type in _ELEVATION_MAPS:
        return flag_outliers(values, ELEVATION_JUMP)
    return list(values)


def promote_top_thickness(values: Sequence[ExtractedValue]) -> list[ExtractedValue]:
    """Promote the topmost, weakly supported thickness reading when it fits the column."""
    usable = [value for value in values if _has_number(value, ("accepted", "low_confidence"))]
    accepted = [value for value in usable if value.status == "accepted"]
    if len(accepted) < 2:
        return list(values)
    column_x = statistics.median(value.x for value in accepted)
    column = sorted(
        (value for value in usable if abs(value.x - column_x) <= COLUMN_WIDTH),
        key=lambda value: value.y,
    )
    if len(column) < 2:
        return list(values)
    top, below = column[0], column[1]
    if top.status != "low_confidence":
        return list(values)
    assert top.value is not None and below.value is not None
    if not PROMOTION_MIN_GAP <= below.value - top.value <= PROMOTION_MAX_GAP:
        return list(values)
    return [
        value.model_copy(update={"status": "accepted"}) if value is top else value
        for value in values
    ]


def flag_outliers(values: Sequence[ExtractedValue], jump: float) -> list[ExtractedValue]:
    """Mark accepted values that differ from the median of their neighbours by more than `jump`."""
    accepted = [value for value in values if _has_number(value, ("accepted",))]
    flagged: set[int] = set()
    for value in accepted:
        neighbours = [
            other.value
            for other in accepted
            if other is not value
            and other.value is not None
            and math.hypot(other.x - value.x, other.y - value.y) <= NEIGHBOUR_RADIUS
        ]
        if len(neighbours) < MIN_NEIGHBOURS or value.value is None:
            continue
        if abs(value.value - statistics.median(neighbours)) > jump:
            flagged.add(id(value))
    return [
        value.model_copy(update={"status": "out_of_range"}) if id(value) in flagged else value
        for value in values
    ]


def _has_number(value: ExtractedValue, statuses: tuple[str, ...]) -> bool:
    return value.value is not None and value.status in statuses
