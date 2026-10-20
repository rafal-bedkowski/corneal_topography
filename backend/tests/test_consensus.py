from ingest.consensus import merge_passes
from ingest.rules import RawToken


def tok(text: str, x: float = 0.45, y: float = 0.5, confidence: float = 1.0) -> RawToken:
    return RawToken(text, confidence, x, y)


def test_a_value_read_by_every_pass_has_full_confidence() -> None:
    values = merge_passes([[tok("558")], [tok("558")], [tok("558")], [tok("558")]], "ct_a")
    assert [(v.text, v.value, v.status, v.confidence) for v in values] == [
        ("558", 558.0, "accepted", 1.0)
    ]


def test_majority_reading_wins_over_a_misread() -> None:
    passes = [[tok("558")], [tok("558")], [tok("568")], [tok("5586")]]
    (value,) = merge_passes(passes, "ct_a")
    assert (value.value, value.status, value.confidence) == (558.0, "accepted", 0.5)


def test_accepted_reading_beats_a_malformed_one_even_with_fewer_votes() -> None:
    passes = [[tok("43.11")], [tok("43.11")], [tok("43.1")], [tok("43.11")]]
    (value,) = merge_passes(passes, "sag_a")
    assert (value.value, value.status) == (43.1, "low_confidence")
    assert value.confidence == 0.25


def test_a_value_read_by_half_the_passes_is_still_accepted() -> None:
    (value,) = merge_passes([[tok("558")], [], [tok("558")], []], "ct_a")
    assert (value.status, value.confidence) == ("accepted", 0.5)


def test_a_value_read_by_a_single_pass_is_low_confidence() -> None:
    (value,) = merge_passes([[tok("558")], [], [], []], "ct_a")
    assert (value.value, value.status, value.confidence) == (558.0, "low_confidence", 0.25)


def test_distant_tokens_stay_separate() -> None:
    passes = [[tok("558", 0.45, 0.5), tok("564", 0.45, 0.6)]]
    values = merge_passes(passes, "ct_a")
    assert [v.value for v in values] == [558.0, 564.0]


def test_values_are_sorted_top_to_bottom_then_left_to_right() -> None:
    passes = [[tok("587", 0.45, 0.7), tok("558", 0.45, 0.5), tok("564", 0.45, 0.6)]]
    assert [v.value for v in merge_passes(passes, "ct_a")] == [558.0, 564.0, 587.0]


def test_position_is_the_cluster_centre() -> None:
    passes = [[tok("558", 0.44, 0.5)], [tok("558", 0.46, 0.5)]]
    (value,) = merge_passes(passes, "ct_a")
    assert round(value.x, 2) == 0.45


def test_unparseable_readings_are_kept_as_flagged() -> None:
    (value,) = merge_passes([[tok("4000")], [tok("4000")]], "ct_a")
    assert (value.status, value.value, value.confidence) == ("out_of_range", None, 1.0)


def test_ignored_labels_keep_each_distinct_text() -> None:
    passes = [[tok("SO OD", 0.9, 0.1)], [tok("0OD", 0.9, 0.1)], [tok("SO OD", 0.9, 0.1)]]
    values = merge_passes(passes, "ct_a")
    assert sorted(v.text for v in values) == ["0OD", "SO OD"]
    assert {v.status for v in values} == {"rejected"}


def test_numbers_win_over_labels_in_the_same_cluster() -> None:
    passes = [[tok("90°")], [tok("558")]]
    (value,) = merge_passes(passes, "ct_a")
    assert value.value == 558.0


def test_no_passes_gives_no_values() -> None:
    assert merge_passes([], "ct_a") == []
