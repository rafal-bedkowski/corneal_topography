import os
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models import ExamIndex, ExamRecord
from tests.conftest import index_path_of, sample_exams


def test_health_reports_exam_count(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "exams": 6}


def test_health_is_503_when_index_missing(
    make_client: Callable[[list[ExamRecord] | None], TestClient],
) -> None:
    response = make_client(None).get("/api/health")
    assert response.status_code == 503
    assert "ingestion" in response.json()["detail"]


def test_data_endpoints_are_503_when_index_missing(
    make_client: Callable[[list[ExamRecord] | None], TestClient],
) -> None:
    missing = make_client(None)
    for path in ("/api/exams", "/api/stats", "/api/exams/train_validation/normal/1"):
        assert missing.get(path).status_code == 503


def test_503_when_index_is_not_json(client: TestClient) -> None:
    index_path_of(client).write_text("{not json", encoding="utf-8")
    response = client.get("/api/health")
    assert response.status_code == 503
    assert "unreadable" in response.json()["detail"]


def test_list_defaults(client: TestClient) -> None:
    body = client.get("/api/exams").json()
    assert (body["total"], body["page"], body["page_size"]) == (6, 1, 24)
    assert [item["exam_id"] for item in body["items"]][:2] == [
        "train_validation/normal/1",
        "train_validation/normal/2",
    ]
    first = body["items"][0]
    assert first["thumbnail_url"] == "/api/exams/train_validation/normal/1/maps/sag_a/image"
    assert first["min_thickness_um"] == 558
    assert first["possible_duplicate_of"] == []


def test_filters_combine_with_and(client: TestClient) -> None:
    assert client.get("/api/exams?label=suspect").json()["total"] == 2
    assert client.get("/api/exams?label=suspect&laterality=OD").json()["total"] == 1
    assert client.get("/api/exams?split=independent_test&label=normal").json()["total"] == 0
    assert client.get("/api/exams?laterality=unknown").json()["total"] == 1


def test_pagination(client: TestClient) -> None:
    body = client.get("/api/exams?page=2&page_size=4").json()
    assert body["total"] == 6
    assert len(body["items"]) == 2
    assert client.get("/api/exams?page=9").json()["items"] == []


def test_sort_by_thickness_puts_missing_last_in_both_orders(client: TestClient) -> None:
    for order in ("asc", "desc"):
        items = client.get(f"/api/exams?sort=min_thickness&order={order}").json()["items"]
        assert items[-1]["exam_id"] == "train_validation/keratoconus/15"
        assert items[-1]["min_thickness_um"] is None
    ascending = client.get("/api/exams?sort=min_thickness&order=asc").json()["items"]
    assert [item["min_thickness_um"] for item in ascending[:3]] == [460, 476, 500]
    descending = client.get("/api/exams?sort=min_thickness&order=desc").json()["items"]
    assert [item["min_thickness_um"] for item in descending[:2]] == [558, 533]


def test_sort_by_case_descending(client: TestClient) -> None:
    items = client.get("/api/exams?order=desc").json()["items"]
    assert items[0]["exam_id"] == "independent_test/suspect/8"


@pytest.mark.parametrize(
    "query",
    [
        "page_size=101",
        "page_size=0",
        "page=0",
        "label=foo",
        "split=bar",
        "laterality=left",
        "sort=x",
    ],
)
def test_invalid_query_is_422(client: TestClient, query: str) -> None:
    assert client.get(f"/api/exams?{query}").status_code == 422


def test_detail_has_seven_maps_with_urls(client: TestClient) -> None:
    body = client.get("/api/exams/train_validation/keratoconus/14").json()
    assert body["label"] == "keratoconus"
    assert set(body["maps"]) == {"sag_a", "sag_p", "elv_a", "elv_p", "ec_a", "ec_p", "ct_a"}
    ct = body["maps"]["ct_a"]
    assert ct["title"] == "Corneal thickness"
    assert ct["unit"] == "µm"
    assert ct["image_url"] == "/api/exams/train_validation/keratoconus/14/maps/ct_a/image"
    assert body["indicators"]["min_thickness_um"] == 460


@pytest.mark.parametrize(
    "path",
    [
        "/api/exams/train_validation/keratoconus/999",
        "/api/exams/nope/keratoconus/14",
        "/api/exams/train_validation/keratoconus/abc",
    ],
)
def test_unknown_exam_is_404(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Exam not found"}


def test_image_is_served_as_jpeg(client: TestClient) -> None:
    response = client.get("/api/exams/train_validation/normal/1/maps/sag_a/image")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content[:2] == b"\xff\xd8"


@pytest.mark.parametrize(
    "path",
    [
        "/api/exams/train_validation/normal/1/maps/nope/image",
        "/api/exams/train_validation/normal/99/maps/sag_a/image",
        "/api/exams/train_validation/normal/..%2f..%2fetc/maps/sag_a/image",
        "/api/exams/..%2f..%2f/normal/1/maps/sag_a/image",
        "/api/exams/train_validation/normal/1/maps/..%2f..%2fexams.json/image",
    ],
)
def test_image_unknown_or_traversal_is_404(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def test_image_outside_dataset_dir_is_never_served(
    make_client: Callable[[list[ExamRecord] | None], TestClient],
) -> None:
    exams = sample_exams()
    exams[0].maps["sag_a"].file = "../exams.json"
    response = make_client(exams).get("/api/exams/train_validation/normal/1/maps/sag_a/image")
    assert response.status_code == 404


def test_missing_image_file_is_404(
    make_client: Callable[[list[ExamRecord] | None], TestClient],
) -> None:
    exams = sample_exams()
    exams[0].maps["sag_a"].file = "gone/Sag_A.jpg"
    response = make_client(exams).get("/api/exams/train_validation/normal/1/maps/sag_a/image")
    assert response.status_code == 404


def test_index_is_reloaded_when_the_file_changes(client: TestClient) -> None:
    assert client.get("/api/health").json()["exams"] == 6
    path = index_path_of(client)
    path.write_text(
        ExamIndex(generated_at="x", exams=sample_exams()[:2]).model_dump_json(), encoding="utf-8"
    )
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert client.get("/api/health").json()["exams"] == 2


def test_cors_allows_the_configured_origin(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
