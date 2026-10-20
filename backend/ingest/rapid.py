"""Text recognition with RapidOCR (ONNX models bundled with the pip package; runs anywhere)."""

import importlib.util
import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ingest.engines import (
    KEY_MAPS,
    OcrUnavailableError,
    Pass,
    Progress,
    map_type_of,
    prepare_image,
)
from ingest.rules import RawToken

MAX_WORKERS = 8
CHUNK_SIZE = 24

# Chosen by greedy selection on the tuning set of the gold sample (see CLAUDE.md, Changelog).
PASSES: tuple[Pass, ...] = (
    Pass("gray3", 3, "gray", KEY_MAPS),
    Pass("invert4", 4, "invert", KEY_MAPS),
    Pass("rgb4", 4, "rgb"),
    Pass("rgb5", 5, "rgb", KEY_MAPS),
    Pass("gray6", 6, "gray", KEY_MAPS),
    Pass("gray4", 4, "gray"),
    Pass("sharpen4", 4, "sharpen", KEY_MAPS),
    Pass("binary4", 4, "binary", KEY_MAPS),
)

_engine: Any = None


def tokens_from_result(
    result: Sequence[Sequence[Any]] | None, width: int, height: int
) -> list[RawToken]:
    """Convert RapidOCR output (`[box, text, score]` per text) to tokens with centre fractions."""
    tokens: list[RawToken] = []
    for box, text, score in result or []:
        xs = [point[0] for point in box]
        ys = [point[1] for point in box]
        tokens.append(
            RawToken(
                str(text),
                float(score),
                (min(xs) + max(xs)) / 2 / width,
                (min(ys) + max(ys)) / 2 / height,
            )
        )
    return tokens


def _init_worker() -> None:
    global _engine
    from rapidocr_onnxruntime import RapidOCR

    _engine = RapidOCR()


def _recognise_chunk(paths: list[str], recognition_pass: Pass) -> list[list[RawToken]]:
    chunk: list[list[RawToken]] = []
    for path in paths:
        with Image.open(path) as source:
            prepared = prepare_image(source, recognition_pass).convert("RGB")
        result, _ = _engine(np.asarray(prepared))
        chunk.append(tokens_from_result(result, prepared.width, prepared.height))
    return chunk


class RapidEngine:
    name = "rapid"

    def unavailable_reason(self) -> str | None:
        if importlib.util.find_spec("rapidocr_onnxruntime") is None:
            return "the `rapidocr-onnxruntime` package is not installed."
        return None

    def recognise(
        self, images: Sequence[Path], progress: Progress | None = None
    ) -> dict[Path, list[list[RawToken]]]:
        result: dict[Path, list[list[RawToken]]] = {image: [] for image in images}
        kinds = {image: map_type_of(image) for image in images}
        workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1))
        try:
            with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
                for number, recognition_pass in enumerate(PASSES, start=1):
                    subset = [i for i in images if recognition_pass.applies_to(kinds[i])]
                    if progress:
                        progress(
                            f"RapidOCR pass {number}/{len(PASSES)} "
                            f"({recognition_pass.name}, {len(subset)} images)"
                        )
                    chunks = [subset[k : k + CHUNK_SIZE] for k in range(0, len(subset), CHUNK_SIZE)]
                    outputs = pool.map(
                        _recognise_chunk,
                        [[str(path) for path in chunk] for chunk in chunks],
                        [recognition_pass] * len(chunks),
                    )
                    for chunk, tokens_per_image in zip(chunks, outputs, strict=True):
                        for image, tokens in zip(chunk, tokens_per_image, strict=True):
                            result[image].append(tokens)
        except OSError as error:
            raise OcrUnavailableError(f"RapidOCR could not start: {error}") from error
        return result
