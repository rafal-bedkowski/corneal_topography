from app.models import MapRecord
from ingest.indicators import compute_indicators, detect_laterality
from tests.factories import accepted, make_maps, value


def test_indicators_from_accepted_values() -> None:
    maps = make_maps(
        thickness=[558, 564, 587],
        curvature=[40.7, 42.4, 41.1],
        extra={
            "elv_a": accepted(-8, 2, 1),
            "elv_p": accepted(8, -27, 5),
        },
    )
    result = compute_indicators(maps)
    assert result.min_thickness_um == 558
    assert result.max_curvature_a_d == 42.4
    assert result.min_curvature_a_d == 40.7
    assert result.curvature_spread_a_d == 1.7
    assert result.max_elevation_a_um == 2
    assert result.max_elevation_p_um == 8


def test_indicators_ignore_values_that_are_not_accepted() -> None:
    maps = make_maps(
        thickness=[500],
        extra={
            "ct_a": [
                *accepted(500),
                value("4000", None, "out_of_range"),
                value("300", 300, "rejected"),
            ]
        },
    )
    assert compute_indicators(maps).min_thickness_um == 500


def test_indicators_are_none_without_accepted_values() -> None:
    result = compute_indicators(make_maps())
    assert result.model_dump() == {
        "min_thickness_um": None,
        "max_curvature_a_d": None,
        "min_curvature_a_d": None,
        "curvature_spread_a_d": None,
        "max_elevation_a_um": None,
        "max_elevation_p_um": None,
    }


def test_zero_is_not_confused_with_missing() -> None:
    maps = make_maps(extra={"elv_a": accepted(0, -3)})
    assert compute_indicators(maps).max_elevation_a_um == 0


def _with_labels(labels: dict[str, list[str]]) -> dict[str, MapRecord]:
    return {
        map_type: MapRecord(file="x.jpg", values=[value(text, None, "rejected") for text in texts])
        for map_type, texts in labels.items()
    }


def test_laterality_majority_vote() -> None:
    maps = make_maps()
    maps["sag_p"] = MapRecord(file="x", values=[value("OD", None, "rejected")])
    maps["ct_a"] = MapRecord(file="x", values=[value("SO OD", None, "rejected")])
    maps["elv_a"] = MapRecord(file="x", values=[value("OS", None, "rejected")])
    assert detect_laterality(maps) == "OD"


def test_laterality_handles_noisy_text() -> None:
    maps = make_maps()
    maps["ct_a"] = MapRecord(file="x", values=[value("0OD", None, "rejected")])
    assert detect_laterality(maps) == "OD"
    maps["ct_a"] = MapRecord(file="x", values=[value("To OS", None, "rejected")])
    assert detect_laterality(maps) == "OS"


def test_laterality_unknown_without_labels() -> None:
    assert detect_laterality(make_maps(thickness=[500])) == "unknown"


def test_laterality_unknown_on_a_tie() -> None:
    maps = make_maps()
    maps["sag_p"] = MapRecord(file="x", values=[value("OD", None, "rejected")])
    maps["ct_a"] = MapRecord(file="x", values=[value("OS", None, "rejected")])
    assert detect_laterality(maps) == "unknown"


def test_laterality_ignores_letters_inside_other_words() -> None:
    maps = make_maps()
    maps["ct_a"] = MapRecord(file="x", values=[value("MODS", None, "rejected")])
    assert detect_laterality(maps) == "unknown"
