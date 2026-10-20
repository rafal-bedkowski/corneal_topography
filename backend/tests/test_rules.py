import pytest

from app.constants import MapType
from ingest.rules import RawToken, classify, is_perimeter_label, normalise_text, strip_padding


def token(text: str, confidence: float = 1.0, x: float = 0.5, y: float = 0.5) -> RawToken:
    return RawToken(text, confidence, x, y)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("−5.9", "-5.9"),
        ("–12", "-12"),
        ("6,1", "6.1"),
        ("+ 5", "+5"),
        ("  +12 ", "+12"),
    ],
)
def test_normalise_text(raw: str, expected: str) -> None:
    assert normalise_text(raw) == expected


@pytest.mark.parametrize("text", ["90°", "120 °", "T", "N", "OD", "OS", "9mm", "SO OD", "350.·S"])
def test_perimeter_by_text(text: str) -> None:
    assert is_perimeter_label(text, 0.5, 0.5)


def test_perimeter_by_position() -> None:
    assert is_perimeter_label("330", 0.93, 0.72)
    assert not is_perimeter_label("330", 0.5, 0.5)


@pytest.mark.parametrize(
    ("map_type", "text", "status", "number"),
    [
        ("sag_a", "43.1", "accepted", 43.1),
        ("sag_a", "43.11", "out_of_range", None),
        ("sag_a", "148.6", "out_of_range", None),
        ("sag_a", "29.9", "out_of_range", 29.9),
        ("sag_a", "75.1", "out_of_range", 75.1),
        ("sag_p", "-6.1", "accepted", -6.1),
        ("sag_p", "6.1", "out_of_range", 6.1),
        ("sag_p", "-2.9", "out_of_range", -2.9),
        ("sag_p", "−5.9", "accepted", -5.9),
        ("elv_a", "+5", "accepted", 5.0),
        ("elv_a", "-27", "accepted", -27.0),
        ("elv_a", "0", "accepted", 0.0),
        ("elv_a", "5", "out_of_range", None),
        ("elv_a", "•15", "out_of_range", None),
        ("elv_a", "+12..-", "out_of_range", None),
        ("elv_p", "+301", "out_of_range", 301.0),
        ("ec_a", "+ 7", "accepted", 7.0),
        ("ec_p", "-300", "accepted", -300.0),
        ("ct_a", "558", "accepted", 558.0),
        ("ct_a", "4000", "out_of_range", None),
        ("ct_a", "299", "out_of_range", 299.0),
        ("ct_a", "901", "out_of_range", 901.0),
        ("ct_a", "-574-", "accepted", 574.0),
        ("ct_a", "487.", "accepted", 487.0),
    ],
)
def test_classify_formats_and_ranges(
    map_type: MapType, text: str, status: str, number: float | None
) -> None:
    result = classify(token(text), map_type)
    assert result.status == status
    assert result.value == number


def test_perimeter_label_is_rejected_whatever_the_map() -> None:
    result = classify(token("90°", x=0.5, y=0.03), "ct_a")
    assert result.status == "rejected"
    assert result.value is None


def test_degree_less_angle_label_outside_the_circle_is_rejected() -> None:
    assert classify(token("330", x=0.93, y=0.72), "ct_a").status == "rejected"


def test_low_confidence_wins_over_format() -> None:
    result = classify(token("476", confidence=0.4), "ct_a")
    assert result.status == "low_confidence"
    assert result.value == 476.0


def test_low_confidence_with_bad_format_has_no_value() -> None:
    result = classify(token("47*6", confidence=0.4), "ct_a")
    assert result.status == "low_confidence"
    assert result.value is None


def test_confidence_is_clamped() -> None:
    assert classify(token("476", confidence=1.2), "ct_a").confidence == 1.0


def test_original_text_is_preserved() -> None:
    assert classify(token("−5.9"), "sag_p").text == "−5.9"


@pytest.mark.parametrize(
    ("map_type", "text", "expected"),
    [
        ("ct_a", "-574-", "574"),
        ("sag_a", "*43.1.", "43.1"),
        ("sag_p", "-5.9-", "-5.9"),
        ("sag_p", "5.9", "5.9"),
        ("elv_a", "+12..-", "+12..-"),
    ],
)
def test_strip_padding(map_type: MapType, text: str, expected: str) -> None:
    assert strip_padding(text, map_type) == expected
