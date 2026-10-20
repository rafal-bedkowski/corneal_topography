"""Text recognition with macOS Vision, via a small Swift helper compiled on first use."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from ingest.engines import (
    OcrUnavailableError,
    Pass,
    Progress,
    map_type_of,
    prepare_image,
)
from ingest.rules import RawToken

HELPER_SOURCE = Path(__file__).with_name("vision_ocr.swift")
HELPER_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"
MAX_WORKERS = 8

PASSES: tuple[Pass, ...] = (
    Pass("rgb3", 3, "rgb"),
    Pass("rgb4", 4, "rgb"),
    Pass("gray4", 4, "gray"),
    Pass("binary4", 4, "binary"),
)


class VisionEngine:
    name = "vision"

    def unavailable_reason(self) -> str | None:
        if sys.platform != "darwin":
            return "macOS Vision runs only on macOS."
        if shutil.which("swiftc") is None:
            return "`swiftc` not found; install the Xcode command line tools."
        return None

    def recognise(
        self, images: Sequence[Path], progress: Progress | None = None
    ) -> dict[Path, list[list[RawToken]]]:
        return recognise_images(images, progress)


def recognise_images(
    images: Sequence[Path], progress: Progress | None = None
) -> dict[Path, list[list[RawToken]]]:
    """Recognise the text of each image in every pass. Returns the tokens per pass and image."""
    helper = _compile_helper()
    result: dict[Path, list[list[RawToken]]] = {image: [] for image in images}
    kinds = {image: map_type_of(image) for image in images}
    for number, recognition_pass in enumerate(PASSES, start=1):
        subset = [image for image in images if recognition_pass.applies_to(kinds[image])]
        if progress:
            progress(
                f"Vision pass {number}/{len(PASSES)} "
                f"({recognition_pass.name}, {len(subset)} images)"
            )
        with tempfile.TemporaryDirectory(prefix="ocr-") as tmp:
            prepared: dict[Path, Path] = {}
            for index, image in enumerate(subset):
                target = Path(tmp) / f"{index}.png"
                with Image.open(image) as source:
                    prepare_image(source, recognition_pass).save(target)
                prepared[target] = image
            for image, tokens in _run_helper(helper, prepared).items():
                result[image].append(tokens)
    return result


def _compile_helper() -> Path:
    swiftc = shutil.which("swiftc")
    if swiftc is None:
        raise OcrUnavailableError("`swiftc` not found. Install the Xcode command line tools.")
    HELPER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    binary = HELPER_CACHE_DIR / "vision_ocr"
    if not binary.exists() or binary.stat().st_mtime < HELPER_SOURCE.stat().st_mtime:
        result = subprocess.run(
            [swiftc, "-O", str(HELPER_SOURCE), "-o", str(binary)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise OcrUnavailableError(f"Compiling the Vision helper failed:\n{result.stderr}")
    return binary


def _run_helper(helper: Path, prepared: dict[Path, Path]) -> dict[Path, list[RawToken]]:
    paths = list(prepared)
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1))
    chunks = [paths[index::workers] for index in range(workers)]
    tokens: dict[Path, list[RawToken]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for chunk_result in pool.map(lambda chunk: _run_chunk(helper, chunk, prepared), chunks):
            tokens.update(chunk_result)
    missing = set(prepared.values()) - set(tokens)
    if missing:
        raise OcrUnavailableError(f"No recognition result for {len(missing)} image(s).")
    return tokens


def _run_chunk(
    helper: Path, chunk: list[Path], prepared: dict[Path, Path]
) -> dict[Path, list[RawToken]]:
    if not chunk:
        return {}
    result = subprocess.run(
        [str(helper)],
        input="\n".join(str(path) for path in chunk),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise OcrUnavailableError(f"Vision helper failed:\n{result.stderr}")
    tokens: dict[Path, list[RawToken]] = {}
    for line in result.stdout.splitlines():
        record = json.loads(line)
        original = prepared[Path(record["path"])]
        if record.get("error"):
            raise OcrUnavailableError(f"Recognition failed for {original}: {record['error']}")
        tokens[original] = [
            RawToken(item["text"], item["confidence"], item["x"], item["y"])
            for item in record["tokens"]
        ]
    return tokens
