import math
import statistics

from fastapi.testclient import TestClient

from app.constants import Label, Split
from app.models import ExamRecord, Indicators
from app.services.statistics import compute_stats, histogram, summarise
from tests.factories import make_exam, value


def exam(
    case: int,
    label: Label = "normal",
    split: Split = "train_validation",
    thickness: float | None = None,
    excluded: bool = False,
) -> ExamRecord:
    record = make_exam(
        split=split, label=label, case=case, indicators=Indicators(min_thickness_um=thickness)
    )
    record.stats_excluded = excluded
    return record


def test_summarise_matches_the_statistics_module() -> None:
    values = [558.0, 533.0, 511.0, 600.0]
    result = summarise(values)
    assert result.n == 4
    assert math.isclose(result.mean or 0, statistics.fmean(values))
    assert result.median == statistics.median(values)
    assert math.isclose(result.std or 0, statistics.stdev(values))
    assert (result.min, result.max) == (511, 600)


def test_summarise_single_value_has_no_std() -> None:
    result = summarise([500.0])
    assert result.n == 1
    assert result.std is None
    assert result.mean == 500


def test_summarise_empty() -> None:
    assert summarise([]).model_dump() == {
        "n": 0,
        "mean": None,
        "median": None,
        "std": None,
        "min": None,
        "max": None,
    }


def test_histogram_fills_gaps_between_bins() -> None:
    result = histogram([405, 410, 445, 501], 20)
    assert [(b.from_, b.count) for b in result.bins] == [
        (400, 2),
        (420, 0),
        (440, 1),
        (460, 0),
        (480, 0),
        (500, 1),
    ]


def test_histogram_of_nothing_has_no_bins() -> None:
    assert histogram([], 20).bins == []


def test_classes_are_ordered_and_counts_add_up() -> None:
    exams = [
        exam(1, "suspect", thickness=500),
        exam(2, "normal", thickness=550),
        exam(3, "normal", thickness=560, excluded=True),
        exam(4, "keratoconus", thickness=450),
    ]
    stats = compute_stats(exams, None)
    assert [c.label for c in stats.classes] == ["normal", "keratoconus", "suspect"]
    normal = stats.classes[0]
    assert (normal.exams, normal.excluded_duplicates) == (1, 1)
    assert normal.indicators["min_thickness_um"].n == 1
    assert normal.indicators["min_thickness_um"].mean == 550


def test_split_filter() -> None:
    exams = [exam(1, split="train_validation"), exam(2, split="independent_test")]
    stats = compute_stats(exams, "independent_test")
    assert sum(c.exams + c.excluded_duplicates for c in stats.classes) == 1


def test_empty_class_yields_zero_counts_not_errors() -> None:
    stats = compute_stats([exam(1, "normal", thickness=500)], None)
    suspect = stats.classes[2]
    assert suspect.exams == 0
    assert suspect.indicators["min_thickness_um"].n == 0
    assert suspect.histograms["min_thickness_um"].bins == []


def test_laterality_counts_and_extraction_counts() -> None:
    first = make_exam(case=1, laterality="OD")
    second = make_exam(case=2, laterality="unknown")
    first.maps["ct_a"].values = [value("500", 500), value("90°", None, "rejected")]
    second.maps["sag_a"].values = [value("43.11", None, "out_of_range")]
    normal = compute_stats([first, second], None).classes[0]
    assert normal.laterality == {"OD": 1, "OS": 0, "unknown": 1}
    assert normal.extraction.model_dump() == {
        "accepted": 1,
        "low_confidence": 0,
        "out_of_range": 1,
        "rejected": 1,
    }


def test_excluded_exams_do_not_count_in_extraction_or_laterality() -> None:
    kept = make_exam(case=1, laterality="OD")
    dropped = make_exam(case=2, laterality="OS")
    dropped.stats_excluded = True
    dropped.maps["ct_a"].values = [value("500", 500)]
    normal = compute_stats([kept, dropped], None).classes[0]
    assert normal.laterality["OS"] == 0
    assert normal.extraction.accepted == 0


def test_stats_endpoint_shape(client: TestClient) -> None:
    body = client.get("/api/stats").json()
    assert [c["label"] for c in body["classes"]] == ["normal", "keratoconus", "suspect"]
    normal = body["classes"][0]
    assert normal["exams"] == 2
    assert normal["indicators"]["min_thickness_um"]["mean"] == 545.5
    assert normal["histograms"]["min_thickness_um"]["bin_width"] == 20
    assert normal["histograms"]["min_thickness_um"]["bins"][0] == {"from": 520, "count": 1}
    assert set(normal["extraction"]) == {"accepted", "low_confidence", "out_of_range", "rejected"}


def test_stats_endpoint_split_filter(client: TestClient) -> None:
    body = client.get("/api/stats?split=independent_test").json()
    assert [c["exams"] for c in body["classes"]] == [0, 0, 2]
    assert client.get("/api/stats?split=nope").status_code == 422
