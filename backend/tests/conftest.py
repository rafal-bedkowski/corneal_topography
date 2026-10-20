from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app
from app.models import ExamIndex, ExamRecord, Indicators
from tests.factories import make_exam


def sample_exams() -> list[ExamRecord]:
    return [
        make_exam(
            "train_validation",
            "normal",
            1,
            "OD",
            indicators=Indicators(min_thickness_um=558, max_curvature_a_d=42.4),
        ),
        make_exam(
            "train_validation",
            "normal",
            2,
            "OS",
            indicators=Indicators(min_thickness_um=533, max_curvature_a_d=46.5),
        ),
        make_exam(
            "train_validation",
            "keratoconus",
            14,
            "OS",
            indicators=Indicators(min_thickness_um=460, max_curvature_a_d=52.5),
        ),
        make_exam("train_validation", "keratoconus", 15, "unknown"),
        make_exam(
            "independent_test",
            "suspect",
            7,
            "OD",
            indicators=Indicators(min_thickness_um=476, max_curvature_a_d=45.2),
        ),
        make_exam(
            "independent_test", "suspect", 8, "OS", indicators=Indicators(min_thickness_um=500)
        ),
    ]


@pytest.fixture
def dataset_dir(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    root.mkdir()
    for exam in sample_exams():
        for record in exam.maps.values():
            target = root / record.file
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (4, 4), "green").save(target, "JPEG")
    return root


@pytest.fixture
def write_index(tmp_path: Path) -> Callable[[list[ExamRecord]], Path]:
    def write(exams: list[ExamRecord]) -> Path:
        path = tmp_path / "exams.json"
        path.write_text(
            ExamIndex(generated_at="2026-01-01T00:00:00+00:00", exams=exams).model_dump_json(),
            encoding="utf-8",
        )
        return path

    return write


@pytest.fixture
def make_client(
    dataset_dir: Path, write_index: Callable[[list[ExamRecord]], Path], tmp_path: Path
) -> Callable[[list[ExamRecord] | None], TestClient]:
    def build(exams: list[ExamRecord] | None = None) -> TestClient:
        index_path = write_index(exams) if exams is not None else tmp_path / "missing.json"
        settings = Settings(
            dataset_dir=dataset_dir, index_path=index_path, cors_origins=("http://localhost:3000",)
        )
        return TestClient(create_app(settings))

    return build


@pytest.fixture
def client(make_client: Callable[[list[ExamRecord] | None], TestClient]) -> TestClient:
    return make_client(sample_exams())


def index_path_of(client: TestClient) -> Path:
    return cast(Settings, cast(FastAPI, client.app).state.settings).index_path
