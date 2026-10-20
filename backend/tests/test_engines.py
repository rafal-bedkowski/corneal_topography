from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from ingest import rapid, vision
from ingest.engines import (
    KEY_MAPS,
    OcrUnavailableError,
    Pass,
    Progress,
    combine,
    map_type_of,
    prepare_image,
    select_engines,
)
from ingest.rules import RawToken


class FakeEngine:
    def __init__(self, name: str, reason: str | None = None, token: str = "1") -> None:
        self.name = name
        self._reason = reason
        self._token = token

    def unavailable_reason(self) -> str | None:
        return self._reason

    def recognise(
        self, images: Any, progress: Progress | None = None
    ) -> dict[Path, list[list[RawToken]]]:
        return {image: [[RawToken(self._token, 1.0, 0.5, 0.5)]] for image in images}


def names(engines: Any) -> list[str]:
    return [engine.name for engine in engines]


def test_every_engine_has_unique_pass_names() -> None:
    for passes in (vision.PASSES, rapid.PASSES):
        assert len({p.name for p in passes}) == len(passes)


def test_the_pass_lists() -> None:
    assert len(vision.PASSES) == 4
    assert all(p.maps is None for p in vision.PASSES)
    assert len(rapid.PASSES) == 8
    extra = [p for p in rapid.PASSES if p.maps is not None]
    assert extra and all(p.maps == KEY_MAPS for p in extra)
    assert sum(p.applies_to("ct_a") for p in rapid.PASSES) == 8
    assert sum(p.applies_to("sag_p") for p in rapid.PASSES) == 2
    assert sum(p.applies_to("ec_a") for p in rapid.PASSES) == 2


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("NOR_1_Sag_A.jpg", "sag_a"),
        ("KCN_14_Sag_P.jpg", "sag_p"),
        ("SUSP_3_Elv_A.jpg", "elv_a"),
        ("NOR_9_Elv_P.jpg", "elv_p"),
        ("NOR_9_EC_A.jpg", "ec_a"),
        ("NOR_9_EC_P.jpg", "ec_p"),
        ("NOR_9_CT_A.jpg", "ct_a"),
    ],
)
def test_map_type_of_file_names(name: str, expected: str) -> None:
    assert map_type_of(Path(name)) == expected


def test_map_type_of_rejects_unknown_files() -> None:
    with pytest.raises(OcrUnavailableError):
        map_type_of(Path("notes.jpg"))


@pytest.mark.parametrize("recognition_pass", [*vision.PASSES, *rapid.PASSES], ids=lambda p: p.name)
def test_prepared_images_have_the_pass_scale(recognition_pass: Pass) -> None:
    source = Image.new("RGB", (10, 8), (200, 30, 30))
    prepared = prepare_image(source, recognition_pass)
    assert prepared.size == (10 * recognition_pass.scale, 8 * recognition_pass.scale)


def test_the_binary_pass_has_two_levels() -> None:
    source = Image.new("L", (4, 4), 0)
    source.paste(255, (0, 0, 2, 4))
    binary = prepare_image(source, Pass("b", 1, "binary"))
    assert {binary.getpixel((x, y)) for x in range(4) for y in range(4)} == {0, 255}


def test_the_invert_pass_inverts_the_gray_pass() -> None:
    source = Image.new("L", (4, 4), 0)
    source.paste(255, (0, 0, 2, 4))
    gray = prepare_image(source, Pass("g", 1, "gray"))
    inverted = prepare_image(source, Pass("i", 1, "invert"))
    for x, y in ((0, 0), (3, 3)):
        assert int(str(gray.getpixel((x, y)))) + int(str(inverted.getpixel((x, y)))) == 255


def test_all_available_engines_are_used_by_default() -> None:
    engines = [FakeEngine("vision"), FakeEngine("rapid")]
    assert names(select_engines(engines, {})) == ["vision", "rapid"]


def test_unavailable_engines_are_skipped_by_default() -> None:
    engines = [FakeEngine("vision", "macOS only"), FakeEngine("rapid")]
    assert names(select_engines(engines, {})) == ["rapid"]


def test_engines_can_be_restricted_by_name() -> None:
    engines = [FakeEngine("vision"), FakeEngine("rapid")]
    assert names(select_engines(engines, {"INGEST_ENGINES": "rapid"})) == ["rapid"]
    assert names(select_engines(engines, {"INGEST_ENGINES": " vision , rapid "})) == [
        "vision",
        "rapid",
    ]


def test_disable_vision_keeps_the_other_engines() -> None:
    engines = [FakeEngine("vision"), FakeEngine("rapid")]
    assert names(select_engines(engines, {"INGEST_DISABLE_VISION": "1"})) == ["rapid"]
    assert names(select_engines(engines, {"INGEST_DISABLE_VISION": "0"})) == ["vision", "rapid"]


def test_an_explicitly_named_engine_that_cannot_run_is_an_error() -> None:
    engines = [FakeEngine("vision", "macOS only"), FakeEngine("rapid")]
    with pytest.raises(OcrUnavailableError, match="'vision' is not available: macOS only"):
        select_engines(engines, {"INGEST_ENGINES": "vision"})


def test_an_unknown_engine_name_is_an_error() -> None:
    with pytest.raises(OcrUnavailableError, match="Unknown OCR engine"):
        select_engines([FakeEngine("rapid")], {"INGEST_ENGINES": "nope"})


def test_no_available_engine_is_an_error_with_the_reasons() -> None:
    engines = [FakeEngine("vision", "macOS only"), FakeEngine("rapid", "not installed")]
    with pytest.raises(OcrUnavailableError, match="vision: macOS only.*rapid: not installed"):
        select_engines(engines, {})


def test_the_disable_vision_shortcut_fails_when_the_rest_is_missing() -> None:
    engines = [FakeEngine("vision"), FakeEngine("rapid", "not installed")]
    with pytest.raises(OcrUnavailableError):
        select_engines(engines, {"INGEST_DISABLE_VISION": "1"})


def test_combine_concatenates_the_passes_of_every_engine() -> None:
    image = Path("x.jpg")
    recognise = combine([FakeEngine("a", token="1"), FakeEngine("b", token="2")])
    passes = recognise([image])[image]
    assert [[t.text for t in p] for p in passes] == [["1"], ["2"]]


def test_vision_is_unavailable_off_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingest.vision.sys.platform", "linux")
    assert "macOS" in (vision.VisionEngine().unavailable_reason() or "")


def test_vision_needs_the_swift_compiler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingest.vision.sys.platform", "darwin")
    monkeypatch.setattr("ingest.vision.shutil.which", lambda _: None)
    assert "swiftc" in (vision.VisionEngine().unavailable_reason() or "")


def test_rapid_reports_a_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingest.rapid.importlib.util.find_spec", lambda _: None)
    assert "rapidocr-onnxruntime" in (rapid.RapidEngine().unavailable_reason() or "")


def test_rapid_is_available_when_installed() -> None:
    assert rapid.RapidEngine().unavailable_reason() is None


def test_rapid_tokens_use_centre_fractions() -> None:
    result: list[list[Any]] = [
        [[[10, 20], [30, 20], [30, 40], [10, 40]], "+12", 0.9],
        [[[0, 0], [100, 0], [100, 50], [0, 50]], "90", "0.5"],
    ]
    first, second = rapid.tokens_from_result(result, 100, 50)
    assert (first.text, first.confidence, first.x, first.y) == ("+12", 0.9, 0.2, 0.6)
    assert (second.x, second.y, second.confidence) == (0.5, 0.5, 0.5)


def test_rapid_tokens_of_an_empty_result() -> None:
    assert rapid.tokens_from_result(None, 10, 10) == []
    assert rapid.tokens_from_result([], 10, 10) == []
