"""Indicators derived from accepted values (spec 4.6) and laterality (spec 4.7)."""

import re
from collections import Counter

from app.constants import Laterality, MapType
from app.models import ExtractedValue, Indicators, MapRecord

_LATERALITY_LABEL = re.compile(r"(?<![A-Za-z])O([DS])(?![A-Za-z])")


def accepted_values(maps: dict[MapType, MapRecord], map_type: MapType) -> list[float]:
    record = maps.get(map_type)
    if record is None:
        return []
    return [
        value.value
        for value in record.values
        if value.status == "accepted" and value.value is not None
    ]


def compute_indicators(maps: dict[MapType, MapRecord]) -> Indicators:
    thickness = accepted_values(maps, "ct_a")
    curvature = accepted_values(maps, "sag_a")
    elevation_a = accepted_values(maps, "elv_a")
    elevation_p = accepted_values(maps, "elv_p")
    return Indicators(
        min_thickness_um=min(thickness, default=None),
        max_curvature_a_d=max(curvature, default=None),
        min_curvature_a_d=min(curvature, default=None),
        curvature_spread_a_d=round(max(curvature) - min(curvature), 1) if curvature else None,
        max_elevation_a_um=max(elevation_a, default=None),
        max_elevation_p_um=max(elevation_p, default=None),
    )


def detect_laterality(maps: dict[MapType, MapRecord]) -> Laterality:
    """Majority vote of the `OD`/`OS` labels found on the exam's maps."""
    votes: Counter[str] = Counter()
    for record in maps.values():
        found = _laterality_on_map(record.values)
        if found is not None:
            votes[found] += 1
    if not votes:
        return "unknown"
    ranked = votes.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "unknown"
    return "OD" if ranked[0][0] == "D" else "OS"


def _laterality_on_map(values: list[ExtractedValue]) -> str | None:
    found = {match.group(1) for value in values for match in _LATERALITY_LABEL.finditer(value.text)}
    return found.pop() if len(found) == 1 else None
