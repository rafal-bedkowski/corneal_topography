"""Text recognition with macOS Vision, via a small Swift helper compiled on first use.

Vision reads these small screenshots unreliably: a value missed at one scale is often found at
another. Every image is therefore recognised in several passes (different scale and contrast
treatment); `ingest.consensus` combines the passes.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps

from ingest.rules import RawToken

HELPER_SOURCE = Path(__file__).with_name("vision_ocr.swift")
HELPER_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"
BINARY_THRESHOLD = 140
MAX_WORKERS = 8

Mode = Literal["rgb", "gray", "binary"]
# Tokens of every pass, per original image path.
Recogniser = Callable[[Sequence[Path]], dict[Path, list[list[RawToken]]]]
Progress = Callable[[str], None]


@dataclass(frozen=True)
class Pass:
    name: str
    scale: int
    mode: Mode


PASSES: tuple[Pass, ...] = (
    Pass("rgb3", 3, "rgb"),
    Pass("rgb4", 4, "rgb"),
    Pass("gray4", 4, "gray"),
    Pass("binary4", 4, "binary"),
)


class OcrUnavailableError(Exception):
    """OCR cannot run on this machine."""


def ensure_macos() -> None:
    if sys.platform != "darwin":
        raise OcrUnavailableError(
            "Ingestion uses macOS Vision for text recognition and runs only on macOS."
        )


def prepare_image(image: Image.Image, recognition_pass: Pass) -> Image.Image:
    size = (image.width * recognition_pass.scale, image.height * recognition_pass.scale)
    if recognition_pass.mode == "rgb":
        return image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    gray = ImageOps.autocontrast(
        image.convert("L").resize(size, Image.Resampling.BICUBIC), cutoff=2
    )
    if recognition_pass.mode == "gray":
        return gray
    return gray.point(lambda value: 255 if value > BINARY_THRESHOLD else 0)


def recognise_images(
    images: Sequence[Path], progress: Progress | None = None
) -> dict[Path, list[list[RawToken]]]:
    """Recognise the text of each image in every pass. Returns the tokens per pass and image."""
    ensure_macos()
    helper = _compile_helper()
    result: dict[Path, list[list[RawToken]]] = {image: [] for image in images}
    for number, recognition_pass in enumerate(PASSES, start=1):
        if progress:
            progress(f"Recognition pass {number}/{len(PASSES)} ({recognition_pass.name})")
        with tempfile.TemporaryDirectory(prefix="ocr-") as tmp:
            prepared: dict[Path, Path] = {}
            for index, image in enumerate(images):
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
