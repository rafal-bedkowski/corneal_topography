import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from PIL import Image

from app.constants import LABEL_DIRS, LABEL_PREFIXES, MAP_SPECS, SPLIT_DIRS, Label, Split
from app.models import ExamIndex
from ingest import cli
from ingest.builder import build_index
from ingest.discovery import discover
from ingest.engines import OcrUnavailableError
from ingest.rules import RawToken


def make_case(root: Path, split: Split, label: Label, case: int, drop: str | None = None) -> Path:
    folder = root / SPLIT_DIRS[split] / SPLIT_DIRS[split] / LABEL_DIRS[label] / f"case{case}"
    folder.mkdir(parents=True)
    for spec in MAP_SPECS:
        if spec.file_suffix == drop:
            continue
        name = f"{LABEL_PREFIXES[label]}_{case}_{spec.file_suffix}.jpg"
        Image.new("RGB", (8, 8), "white").save(folder / name, "JPEG")
    return folder


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    make_case(root, "train_validation", "normal", 1)
    make_case(root, "train_validation", "keratoconus", 2)
    make_case(root, "independent_test", "suspect", 1)
    (root / ".DS_Store").write_text("x")
    (root / SPLIT_DIRS["train_validation"]).joinpath(".DS_Store").write_text("x")
    return root


def fake_ocr(images: Sequence[Path]) -> dict[Path, list[list[RawToken]]]:
    tokens: dict[Path, list[list[RawToken]]] = {}
    for image in images:
        if image.name.endswith("CT_A.jpg"):
            tokens[image] = [
                [
                    RawToken("OD", 1.0, 0.9, 0.1),
                    RawToken("558", 1.0, 0.45, 0.5),
                    RawToken("90°", 1.0, 0.5, 0.03),
                    RawToken("4000", 1.0, 0.45, 0.6),
                ]
            ]
        else:
            tokens[image] = [[]]
    return tokens


def test_discovery_finds_all_cases_in_order(dataset: Path) -> None:
    result = discover(dataset)
    assert [(e.split, e.label, e.case) for e in result.exams] == [
        ("train_validation", "normal", 1),
        ("train_validation", "keratoconus", 2),
        ("independent_test", "suspect", 1),
    ]
    assert result.skipped == []
    assert len(result.exams[0].files) == 7


def test_same_case_number_in_different_places_is_not_a_clash(dataset: Path) -> None:
    ids = [(e.split, e.label, e.case) for e in discover(dataset).exams]
    assert len(set(ids)) == 3


def test_case_with_missing_file_is_skipped_and_reported(dataset: Path) -> None:
    make_case(dataset, "train_validation", "normal", 5, drop="EC_P")
    result = discover(dataset)
    assert len(result.exams) == 3
    assert len(result.skipped) == 1
    assert "missing: NOR_5_EC_P.jpg" in result.skipped[0].reason


def test_case_with_unexpected_file_is_skipped(dataset: Path) -> None:
    folder = make_case(dataset, "train_validation", "normal", 6)
    (folder / "notes.txt").write_text("x")
    result = discover(dataset)
    assert [s.path.endswith("case6") for s in result.skipped] == [True]
    assert "unexpected: notes.txt" in result.skipped[0].reason


def test_wrong_prefix_counts_as_missing(dataset: Path) -> None:
    folder = make_case(dataset, "train_validation", "normal", 7)
    (folder / "NOR_7_CT_A.jpg").rename(folder / "KCN_7_CT_A.jpg")
    assert len(discover(dataset).skipped) == 1


def test_non_case_entries_and_files_are_ignored(dataset: Path) -> None:
    label_dir = dataset / SPLIT_DIRS["train_validation"] / SPLIT_DIRS["train_validation"]
    (label_dir / "Normal" / "readme.txt").write_text("x")
    (label_dir / "Normal" / "other").mkdir()
    result = discover(dataset)
    assert len(result.exams) == 3
    assert result.skipped == []


def test_discovery_on_an_empty_directory(tmp_path: Path) -> None:
    result = discover(tmp_path)
    assert result.exams == []


def test_build_index_applies_rules_and_indicators(dataset: Path) -> None:
    result = build_index(dataset, fake_ocr)
    assert len(result.index.exams) == 3
    exam = result.index.exams[0]
    assert exam.exam_id == "train_validation/normal/1"
    assert exam.laterality == "OD"
    assert exam.indicators.min_thickness_um == 558
    statuses = {v.text: v.status for v in exam.maps["ct_a"].values}
    assert statuses == {
        "OD": "rejected",
        "558": "accepted",
        "90°": "rejected",
        "4000": "out_of_range",
    }
    assert result.value_statuses["accepted"] == 3
    assert exam.maps["ct_a"].file.endswith("NOR_1_CT_A.jpg")


def test_write_index_is_atomic_and_valid(dataset: Path, tmp_path: Path) -> None:
    index = build_index(dataset, fake_ocr).index
    target = tmp_path / "out" / "exams.json"
    cli.write_index_atomically(index, target)
    assert ExamIndex.model_validate(json.loads(target.read_text())).exams[0].case == 1
    assert [p.name for p in target.parent.iterdir()] == ["exams.json"]


def test_failed_write_leaves_no_partial_file(tmp_path: Path) -> None:
    target = tmp_path / "exams.json"
    target.write_text("old")

    class Broken:
        def model_dump_json(self) -> str:
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        cli.write_index_atomically(Broken(), target)  # type: ignore[arg-type]
    assert target.read_text() == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["exams.json"]


def test_cli_runs_end_to_end_with_a_fake_recogniser(
    dataset: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "exams.json"
    code = cli.run(["--dataset-dir", str(dataset), "--output", str(output)], recognise=fake_ocr)
    assert code == 0
    assert "Exams indexed: 3" in capsys.readouterr().out
    assert len(ExamIndex.model_validate_json(output.read_text()).exams) == 3


def test_cli_exits_when_no_engine_is_available(
    dataset: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_engine() -> None:
        raise OcrUnavailableError(
            "No OCR engine is available. vision: macOS Vision runs only on macOS."
        )

    monkeypatch.setattr(cli, "default_recogniser", no_engine)
    output = tmp_path / "exams.json"
    code = cli.run(["--dataset-dir", str(dataset), "--output", str(output)])
    assert code == 1
    assert "No OCR engine is available" in capsys.readouterr().err
    assert not output.exists()


def test_cli_reports_a_missing_dataset_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    code = cli.run(["--dataset-dir", str(tmp_path / "nope"), "--output", str(tmp_path / "o.json")])
    assert code == 1
    assert "not found" in capsys.readouterr().err
