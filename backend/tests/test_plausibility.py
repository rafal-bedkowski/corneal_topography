from app.models import ExtractedValue
from ingest.plausibility import flag_outliers, promote_top_thickness, refine
from tests.factories import value


def at(number: float, x: float, y: float, status: str = "accepted") -> ExtractedValue:
    return value(str(number), number, status, x=x, y=y)


def statuses(values: list[ExtractedValue]) -> list[str]:
    return [v.status for v in values]


def test_top_thickness_is_promoted_when_it_fits_the_column() -> None:
    values = [
        at(375, 0.51, 0.51, "low_confidence"),
        at(415, 0.51, 0.60, "low_confidence"),
        at(603, 0.51, 0.80),
        at(700, 0.50, 0.89),
    ]
    assert statuses(promote_top_thickness(values)) == [
        "accepted",
        "low_confidence",
        "accepted",
        "accepted",
    ]


def test_top_thickness_is_promoted_against_an_accepted_neighbour() -> None:
    values = [at(558, 0.5, 0.5, "low_confidence"), at(564, 0.5, 0.6), at(587, 0.5, 0.7)]
    assert promote_top_thickness(values)[0].status == "accepted"


def test_no_promotion_when_the_gap_is_too_small_or_too_large() -> None:
    small = [at(560, 0.5, 0.5, "low_confidence"), at(562, 0.5, 0.6), at(587, 0.5, 0.7)]
    large = [at(300, 0.5, 0.5, "low_confidence"), at(500, 0.5, 0.6), at(587, 0.5, 0.7)]
    assert promote_top_thickness(small)[0].status == "low_confidence"
    assert promote_top_thickness(large)[0].status == "low_confidence"


def test_gap_limits_are_inclusive() -> None:
    low = [at(495, 0.5, 0.5, "low_confidence"), at(500, 0.5, 0.6), at(587, 0.5, 0.7)]
    high = [at(350, 0.5, 0.5, "low_confidence"), at(500, 0.5, 0.6), at(587, 0.5, 0.7)]
    assert promote_top_thickness(low)[0].status == "accepted"
    assert promote_top_thickness(high)[0].status == "accepted"


def test_no_promotion_when_the_value_is_not_above_the_next_one() -> None:
    values = [at(500, 0.5, 0.6), at(450, 0.5, 0.5, "low_confidence"), at(587, 0.5, 0.7)]
    # the weak value is above (smaller y) but is not the smaller one only if its number is larger
    larger = [at(620, 0.5, 0.5, "low_confidence"), at(500, 0.5, 0.6), at(587, 0.5, 0.7)]
    assert promote_top_thickness(larger)[0].status == "low_confidence"
    assert promote_top_thickness(values)[1].status == "accepted"


def test_no_promotion_outside_the_column() -> None:
    values = [at(450, 0.9, 0.5, "low_confidence"), at(500, 0.5, 0.6), at(587, 0.5, 0.7)]
    assert promote_top_thickness(values)[0].status == "low_confidence"


def test_no_promotion_with_a_column_of_fewer_than_two_values() -> None:
    assert (
        promote_top_thickness([at(450, 0.5, 0.5, "low_confidence")])[0].status == "low_confidence"
    )
    one_accepted = [at(450, 0.5, 0.5, "low_confidence"), at(500, 0.5, 0.6)]
    assert promote_top_thickness(one_accepted)[0].status == "low_confidence"


def test_promotion_ignores_other_statuses() -> None:
    values = [
        value("4000", None, "out_of_range", x=0.5, y=0.45),
        at(450, 0.5, 0.5, "low_confidence"),
        at(500, 0.5, 0.6),
        at(587, 0.5, 0.7),
    ]
    assert promote_top_thickness(values)[1].status == "accepted"


def test_elevation_value_far_from_its_neighbours_is_flagged() -> None:
    values = [at(n, 0.5 + dx, 0.5 + dy) for n, dx, dy in [(2, 0.1, 0), (3, -0.1, 0), (1, 0, 0.1)]]
    values.append(at(160, 0.5, 0.5))
    result = flag_outliers(values, 100.0)
    assert statuses(result) == ["accepted", "accepted", "accepted", "out_of_range"]


def test_curvature_misread_is_flagged() -> None:
    values = [at(n, 0.5 + dx, 0.5) for n, dx in [(50.2, 0.05), (52.0, -0.05), (48.6, 0.1)]]
    values.append(at(69.2, 0.5, 0.55))
    assert flag_outliers(values, 12.0)[-1].status == "out_of_range"


def test_value_exactly_at_the_threshold_is_kept() -> None:
    neighbours = [at(0, 0.5 + dx, 0.5) for dx in (0.05, -0.05, 0.1)]
    values = [*neighbours, at(100, 0.5, 0.55)]
    assert flag_outliers(values, 100.0)[-1].status == "accepted"
    values = [*neighbours, at(100.5, 0.5, 0.55)]
    assert flag_outliers(values, 100.0)[-1].status == "out_of_range"


def test_fewer_than_three_neighbours_are_not_checked() -> None:
    values = [at(0, 0.45, 0.5), at(1, 0.55, 0.5), at(500, 0.5, 0.5)]
    assert statuses(flag_outliers(values, 100.0)) == ["accepted", "accepted", "accepted"]


def test_distant_values_are_not_neighbours() -> None:
    values = [at(0, 0.1, 0.1), at(0, 0.12, 0.1), at(0, 0.1, 0.12), at(500, 0.9, 0.9)]
    assert flag_outliers(values, 100.0)[-1].status == "accepted"


def test_only_accepted_values_count_as_neighbours() -> None:
    values = [at(n, 0.5 + dx, 0.5, "low_confidence") for n, dx in [(0, 0.05), (0, -0.05), (0, 0.1)]]
    values.append(at(500, 0.5, 0.55))
    assert flag_outliers(values, 100.0)[-1].status == "accepted"


def test_refine_uses_the_rule_of_the_map_type() -> None:
    neighbours = [at(0, 0.5 + dx, 0.5) for dx in (0.05, -0.05, 0.1)]
    values = [*neighbours, at(50, 0.5, 0.55)]
    assert refine(values, "sag_a")[-1].status == "out_of_range"  # 50 D jump
    assert refine(values, "elv_a")[-1].status == "accepted"  # below 100 µm
    assert refine(values, "ct_a")[-1].status == "accepted"
