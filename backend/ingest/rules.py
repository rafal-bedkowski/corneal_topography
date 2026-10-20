"""Acceptance rules for OCR tokens (spec 4.5)."""

import math
import re
from dataclasses import dataclass

from app.constants import MapType, ValueStatus
from app.models import ExtractedValue

MIN_CONFIDENCE = 0.5
PERIMETER_RADIUS = 0.42  # fraction of the image width, measured from the image centre

_MINUS_SIGNS = str.maketrans({"−": "-", "–": "-", "—": "-", ",": "."})
_DEGREE_SIGNS = ("°", "º", "˚")
_LETTER = re.compile(r"[^\W\d_]")
_SIGN_GAP = re.compile(r"^([+-])\s+(?=\d)")
_POSITIVE_CORE = re.compile(r"^[^\d]*(\d[\d.]*\d|\d)[^\d]*$")
_NEGATIVE_CORE = re.compile(r"^[^\d-]*(-?)[^\d]*(\d[\d.]*\d|\d)[^\d]*$")


@dataclass(frozen=True)
class RawToken:
    text: str
    confidence: float
    x: float
    y: float


@dataclass(frozen=True)
class _Rule:
    pattern: re.Pattern[str]
    low: float
    high: float


_DECIMAL = re.compile(r"^-?\d{1,2}\.\d$")
_SIGNED_INT = re.compile(r"^(?:[+-]\d{1,3}|0)$")
_THICKNESS = re.compile(r"^\d{3}$")

_RULES: dict[MapType, _Rule] = {
    "sag_a": _Rule(_DECIMAL, 30.0, 75.0),
    "sag_p": _Rule(_DECIMAL, -15.0, -3.0),
    "elv_a": _Rule(_SIGNED_INT, -300, 300),
    "elv_p": _Rule(_SIGNED_INT, -300, 300),
    "ec_a": _Rule(_SIGNED_INT, -300, 300),
    "ec_p": _Rule(_SIGNED_INT, -300, 300),
    "ct_a": _Rule(_THICKNESS, 300, 900),
}


def normalise_text(text: str) -> str:
    cleaned = text.strip().translate(_MINUS_SIGNS)
    return _SIGN_GAP.sub(r"\1", cleaned)


def strip_padding(text: str, map_type: MapType) -> str:
    """Drop box borders that the OCR read as characters around a value (`-574-`, `487.`).

    Applied to thickness and curvature only; posterior curvature keeps a leading minus.
    Elevation values keep the strict format because their sign carries the meaning.
    """
    if map_type in ("sag_a", "ct_a"):
        match = _POSITIVE_CORE.match(text)
        return match.group(1) if match else text
    if map_type == "sag_p":
        match = _NEGATIVE_CORE.match(text)
        return f"{match.group(1)}{match.group(2)}" if match else text
    return text


def is_perimeter_label(text: str, x: float, y: float) -> bool:
    """Angle labels, axis letters, `OD`/`OS`, `9mm` and anything else outside the map circle."""
    if any(sign in text for sign in _DEGREE_SIGNS) or _LETTER.search(text):
        return True
    return math.hypot(x - 0.5, y - 0.5) > PERIMETER_RADIUS


def classify(token: RawToken, map_type: MapType) -> ExtractedValue:
    text = normalise_text(token.text)
    if is_perimeter_label(text, token.x, token.y):
        return _build(token, None, "rejected")
    rule = _RULES[map_type]
    parsed = _parse(strip_padding(text, map_type), rule)
    if token.confidence < MIN_CONFIDENCE:
        return _build(token, parsed, "low_confidence")
    if parsed is None or not rule.low <= parsed <= rule.high:
        return _build(token, parsed, "out_of_range")
    return _build(token, parsed, "accepted")


def _parse(text: str, rule: _Rule) -> float | None:
    if rule.pattern.fullmatch(text) is None:
        return None
    return float(text)


def _build(token: RawToken, value: float | None, status: ValueStatus) -> ExtractedValue:
    return ExtractedValue(
        text=token.text,
        value=value,
        confidence=min(max(token.confidence, 0.0), 1.0),
        x=token.x,
        y=token.y,
        status=status,
    )
