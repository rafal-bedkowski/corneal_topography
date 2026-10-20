"""Shared pieces of the OCR engines.

Every engine reads each image in several passes (different scale and contrast treatment). A value
missed in one pass is often found in another, so `ingest.consensus` combines all passes of all
engines by voting. The four maps that feed the indicators get more passes than the other maps.
"""

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from PIL import Image, ImageFilter, ImageOps

from app.constants import MAP_SPECS, MapType
from ingest.rules import RawToken

BINARY_THRESHOLD = 140

Mode = Literal["rgb", "gray", "binary", "invert", "sharpen"]
# Tokens of every pass, per original image path.
Recogniser = Callable[[Sequence[Path]], dict[Path, list[list[RawToken]]]]
Progress = Callable[[str], None]

# The indicators come from these four maps.
KEY_MAPS: frozenset[MapType] = frozenset({"ct_a", "sag_a", "elv_a", "elv_p"})


class OcrUnavailableError(Exception):
    """OCR cannot run on this machine."""


@dataclass(frozen=True)
class Pass:
    name: str
    scale: int
    mode: Mode
    maps: frozenset[MapType] | None = None  # None: every map

    def applies_to(self, map_type: MapType) -> bool:
        return self.maps is None or map_type in self.maps


class Engine(Protocol):
    name: str

    def unavailable_reason(self) -> str | None:
        """Why the engine cannot run here, or `None` when it can."""

    def recognise(
        self, images: Sequence[Path], progress: Progress | None = None
    ) -> dict[Path, list[list[RawToken]]]:
        """Tokens of every pass the engine runs, per image."""


def map_type_of(image: Path) -> MapType:
    """The map type encoded in a file name such as `NOR_1_Elv_A.jpg`."""
    for spec in MAP_SPECS:
        if image.stem.endswith(f"_{spec.file_suffix}"):
            return spec.map_type
    raise OcrUnavailableError(f"Unrecognised map file name: {image.name}")


def prepare_image(image: Image.Image, recognition_pass: Pass) -> Image.Image:
    size = (image.width * recognition_pass.scale, image.height * recognition_pass.scale)
    if recognition_pass.mode == "rgb":
        return image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    if recognition_pass.mode == "sharpen":
        enlarged = image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
        return enlarged.filter(ImageFilter.UnsharpMask(radius=3, percent=250, threshold=2))
    gray = ImageOps.autocontrast(
        image.convert("L").resize(size, Image.Resampling.BICUBIC), cutoff=2
    )
    if recognition_pass.mode == "gray":
        return gray
    if recognition_pass.mode == "invert":
        return ImageOps.invert(gray)
    return gray.point(lambda value: 255 if value > BINARY_THRESHOLD else 0)


def select_engines(
    candidates: Sequence[Engine], environment: Mapping[str, str] | None = None
) -> list[Engine]:
    """Pick the engines to run.

    `INGEST_ENGINES` (comma separated names) restricts the choice; `INGEST_DISABLE_VISION=1` is a
    shortcut for every engine except `vision`. Engines that cannot run here are skipped, unless
    they were named explicitly, which is an error.
    """
    env = os.environ if environment is None else environment
    names = [part.strip() for part in env.get("INGEST_ENGINES", "").split(",") if part.strip()]
    known = {engine.name for engine in candidates}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise OcrUnavailableError(
            f"Unknown OCR engine(s): {', '.join(unknown)}. "
            f"Known engines: {', '.join(sorted(known))}."
        )
    if not names and env.get("INGEST_DISABLE_VISION") == "1":
        names = [engine.name for engine in candidates if engine.name != "vision"]
    chosen = [engine for engine in candidates if not names or engine.name in names]

    selected: list[Engine] = []
    reasons: list[str] = []
    for engine in chosen:
        reason = engine.unavailable_reason()
        if reason is None:
            selected.append(engine)
        else:
            reasons.append(f"{engine.name}: {reason}")
            if engine.name in names:
                raise OcrUnavailableError(f"OCR engine '{engine.name}' is not available: {reason}")
    if not selected:
        raise OcrUnavailableError("No OCR engine is available. " + " ".join(reasons))
    return selected


def combine(engines: Sequence[Engine], progress: Progress | None = None) -> Recogniser:
    """A recogniser whose passes are the passes of every engine."""

    def recognise(images: Sequence[Path]) -> dict[Path, list[list[RawToken]]]:
        merged: dict[Path, list[list[RawToken]]] = {image: [] for image in images}
        for engine in engines:
            for image, passes in engine.recognise(images, progress).items():
                merged[image].extend(passes)
        return merged

    return recognise
