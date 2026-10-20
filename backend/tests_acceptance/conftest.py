"""Acceptance tests run against the real dataset and the index built by `python -m ingest`.

They need `dataset/archive` and `backend/data/exams.json`; a missing index fails the run loudly.
Run with `.venv/bin/pytest tests_acceptance`.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import REPO_ROOT, Settings
from app.main import create_app
from app.models import ExamIndex, ExamRecord

GOLD_PATH = REPO_ROOT / "input_data" / "gold" / "gold_sample.json"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def index(settings: Settings) -> ExamIndex:
    assert settings.index_path.is_file(), f"Run the ingestion first: {settings.index_path} missing"
    return ExamIndex.model_validate_json(settings.index_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def exams(index: ExamIndex) -> dict[str, ExamRecord]:
    return {exam.exam_id: exam for exam in index.exams}


@pytest.fixture(scope="session")
def client(settings: Settings, index: ExamIndex) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture(scope="session")
def gold() -> list[dict[str, object]]:
    data = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    exams: list[dict[str, object]] = data["exams"]
    return exams


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
