import json
from pathlib import Path
from typing import Any

import pytest

from app.models import ExamIndex, Indicators
from ingest import evaluate
from ingest.token_cache import with_cache
from tests.factories import make_exam

GOLD_ITEM: dict[str, Any] = {
    "exam_id": "train_validation/normal/1",
    "set": "tuning",
    "laterality": "OD",
    "indicators": {
        "min_thickness_um": [558],
        "max_curvature_a_d": [42.4, 42.5],
        "min_curvature_a_d": None,
        "max_elevation_a_um": [2],
        "max_elevation_p_um": [8],
    },
}


def index_with(indicators: Indicators, laterality: str = "OD") -> ExamIndex:
    exam = make_exam(indicators=indicators)
    exam.laterality = laterality  # type: ignore[assignment]
    return ExamIndex(generated_at="x", exams=[exam])


def test_score_counts_correct_fields_and_skips_null_gold() -> None:
    result = evaluate.score(
        index_with(
            Indicators(
                min_thickness_um=558,
                max_curvature_a_d=42.5,
                min_curvature_a_d=1.0,
                max_elevation_a_um=3,
                max_elevation_p_um=None,
            )
        ),
        [GOLD_ITEM],
    )
    assert (result.correct, result.scored) == (3, 5)  # laterality, thickness, curvature
    assert result.by_field["max_elevation_a_um"] == (0, 1)
    assert "min_curvature_a_d" not in result.by_field
    assert result.ratio == pytest.approx(0.6)


def test_a_wrong_laterality_is_scored() -> None:
    result = evaluate.score(index_with(Indicators(), laterality="OS"), [GOLD_ITEM])
    assert result.by_field["laterality"] == (0, 1)


def test_select_filters_by_set() -> None:
    gold = [{**GOLD_ITEM, "set": "tuning"}, {**GOLD_ITEM, "set": "holdout"}]
    assert len(evaluate.select(gold, "tuning")) == 1
    assert len(evaluate.select(gold, "holdout")) == 1
    assert len(evaluate.select(gold, "all")) == 2


def test_the_gold_sample_has_the_agreed_shape() -> None:
    gold = evaluate.load_gold()
    assert len(gold) == 30
    assert sum(item["set"] == "tuning" for item in gold) == 20
    assert sum(item["set"] == "holdout" for item in gold) == 10
    assert len({item["exam_id"] for item in gold}) == 30
    for item in gold:
        assert item["laterality"] in ("OD", "OS")
        assert set(item["indicators"]) == set(evaluate.INDICATOR_FIELDS)
        for accepted in item["indicators"].values():
            assert accepted is None or (isinstance(accepted, list) and accepted)


def test_the_cli_prints_the_score(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    gold_ids = {item["exam_id"] for item in evaluate.load_gold()}
    exams = []
    for exam_id in sorted(gold_ids):
        split, label, case = exam_id.split("/")
        exams.append(make_exam(split=split, label=label, case=int(case)))
    path = tmp_path / "index.json"
    path.write_text(ExamIndex(generated_at="x", exams=exams).model_dump_json(), encoding="utf-8")
    assert evaluate.run(["--index", str(path), "--set", "holdout"]) == 0
    assert capsys.readouterr().out.startswith("holdout: ")


def test_token_cache_writes_then_reuses(tmp_path: Path) -> None:
    from ingest.rules import RawToken

    image = tmp_path / "a" / "x.jpg"
    calls: list[int] = []

    def recognise(images: Any) -> dict[Path, list[list[RawToken]]]:
        calls.append(1)
        return {path: [[RawToken("558", 1.0, 0.5, 0.5)]] for path in images}

    cache = tmp_path / "tokens.json"
    wrapped = with_cache(recognise, cache, tmp_path)
    first = wrapped([image])
    second = wrapped([image])
    assert calls == [1]
    assert first == second
    assert json.loads(cache.read_text())["a/x.jpg"] == [[["558", 1.0, 0.5, 0.5]]]


def test_token_cache_recognises_again_for_new_images(tmp_path: Path) -> None:
    from ingest.rules import RawToken

    calls: list[int] = []

    def recognise(images: Any) -> dict[Path, list[list[RawToken]]]:
        calls.append(len(list(images)))
        return {path: [[]] for path in images}

    wrapped = with_cache(recognise, tmp_path / "tokens.json", tmp_path)
    wrapped([tmp_path / "a.jpg"])
    wrapped([tmp_path / "a.jpg", tmp_path / "b.jpg"])
    assert calls == [1, 2]
