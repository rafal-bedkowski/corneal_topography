"""AC9-AC17 against the real index through the FastAPI test client."""

import statistics
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models import ExamRecord


def test_ac9_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "exams": 573}


def test_ac10_default_list(client: TestClient) -> None:
    body = client.get("/api/exams").json()
    assert (body["total"], body["page"], body["page_size"], len(body["items"])) == (573, 1, 24, 24)


def test_ac10_last_page_has_the_remainder(client: TestClient) -> None:
    body = client.get("/api/exams?page=24").json()
    assert len(body["items"]) == 573 - 23 * 24
    assert client.get("/api/exams?page=25").json()["items"] == []


def test_ac11_filters(client: TestClient) -> None:
    assert client.get("/api/exams?label=suspect").json()["total"] == 173
    assert client.get("/api/exams?split=independent_test").json()["total"] == 150
    assert client.get("/api/exams?split=independent_test&label=normal").json()["total"] == 50
    od = client.get("/api/exams?laterality=OD").json()["total"]
    os_ = client.get("/api/exams?laterality=OS").json()["total"]
    unknown = client.get("/api/exams?laterality=unknown").json()["total"]
    assert od + os_ + unknown == 573 and od > 0 and os_ > 0


@pytest.mark.parametrize("order", ["asc", "desc"])
def test_ac12_null_thickness_is_last(client: TestClient, order: str) -> None:
    items: list[dict[str, Any]] = []
    for page in range(1, 7):
        items += client.get(
            f"/api/exams?sort=min_thickness&order={order}&page={page}&page_size=100"
        ).json()["items"]
    assert len(items) == 573
    values = [i["min_thickness_um"] for i in items]
    firsts_none = next((n for n, v in enumerate(values) if v is None), len(values))
    assert all(v is None for v in values[firsts_none:])
    real = [v for v in values if v is not None]
    assert real == sorted(real, reverse=order == "desc")


@pytest.mark.parametrize(
    "query", ["page_size=101", "page=0", "label=foo", "split=bar", "laterality=left", "sort=x"]
)
def test_ac13_invalid_queries(client: TestClient, query: str) -> None:
    assert client.get(f"/api/exams?{query}").status_code == 422


def test_ac14_detail_and_unknown(client: TestClient) -> None:
    body = client.get("/api/exams/train_validation/keratoconus/14").json()
    assert len(body["maps"]) == 7
    assert all(m["image_url"].endswith("/image") for m in body["maps"].values())
    assert client.get("/api/exams/train_validation/keratoconus/9999").status_code == 404


def test_ac15_every_image_endpoint_serves_a_jpeg_for_a_sample(client: TestClient) -> None:
    for exam_id in ("train_validation/normal/1", "independent_test/suspect/50"):
        detail = client.get(f"/api/exams/{exam_id}").json()
        for map_type in detail["maps"]:
            response = client.get(f"/api/exams/{exam_id}/maps/{map_type}/image")
            assert response.status_code == 200, (exam_id, map_type)
            assert response.headers["content-type"] == "image/jpeg"
            assert response.content[:2] == b"\xff\xd8"


@pytest.mark.parametrize(
    "path",
    [
        "/api/exams/train_validation/normal/1/maps/nope/image",
        "/api/exams/train_validation/normal/999/maps/sag_a/image",
        "/api/exams/train_validation/normal/..%2f..%2f..%2fREADME.md/maps/sag_a/image",
        "/api/exams/..%2f..%2f/normal/1/maps/sag_a/image",
        "/api/exams/train_validation/normal/1/maps/..%2f..%2f..%2f..%2fREADME.md/image",
    ],
)
def test_ac15_unknown_and_traversal_are_404(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def _all_exams(client: TestClient) -> list[ExamRecord]:
    return list(client.app.state.store.exams())  # type: ignore[attr-defined]


def test_ac16_stats_class_sizes_and_order(client: TestClient) -> None:
    body = client.get("/api/stats").json()
    assert [c["label"] for c in body["classes"]] == ["normal", "keratoconus", "suspect"]
    assert [c["exams"] + c["excluded_duplicates"] for c in body["classes"]] == [200, 200, 173]


def test_ac16_stats_match_values_recomputed_from_the_index(client: TestClient) -> None:
    exams = _all_exams(client)
    body = client.get("/api/stats").json()
    for cls in body["classes"]:
        included = [e for e in exams if e.label == cls["label"] and not e.stats_excluded]
        assert cls["exams"] == len(included)
        for field, stats in cls["indicators"].items():
            values = [getattr(e.indicators, field) for e in included]
            values = [v for v in values if v is not None]
            assert stats["n"] == len(values)
            if values:
                assert stats["mean"] == pytest.approx(statistics.fmean(values))
                assert stats["median"] == pytest.approx(statistics.median(values))
                assert (stats["min"], stats["max"]) == (min(values), max(values))
            if len(values) >= 2:
                assert stats["std"] == pytest.approx(statistics.stdev(values))
            else:
                assert stats["std"] is None
        histogram = cls["histograms"]["min_thickness_um"]
        thickness = [
            e.indicators.min_thickness_um for e in included if e.indicators.min_thickness_um
        ]
        assert sum(b["count"] for b in histogram["bins"]) == len(thickness)


def test_ac17_independent_test_split_has_50_per_class(client: TestClient) -> None:
    body = client.get("/api/stats?split=independent_test").json()
    assert [c["exams"] + c["excluded_duplicates"] for c in body["classes"]] == [50, 50, 50]
    assert client.get("/api/stats?split=nope").status_code == 422


def test_ac29_excluded_exams_stay_visible_with_flags(client: TestClient) -> None:
    excluded = [e for e in _all_exams(client) if e.stats_excluded]
    assert excluded
    for exam in excluded[:5]:
        summary = next(
            item
            for item in client.get(
                f"/api/exams?split={exam.split}&label={exam.label}&page_size=100&page=1"
            ).json()["items"]
            + client.get(
                f"/api/exams?split={exam.split}&label={exam.label}&page_size=100&page=2"
            ).json()["items"]
            if item["exam_id"] == exam.exam_id
        )
        assert summary["stats_excluded"] is True
        assert summary["possible_duplicate_of"] == exam.possible_duplicate_of
        detail = client.get(f"/api/exams/{exam.exam_id}").json()
        assert detail["stats_excluded"] is True
        assert detail["stats_exclusion_reason"] == exam.stats_exclusion_reason
        assert detail["possible_duplicate_of"] == exam.possible_duplicate_of
