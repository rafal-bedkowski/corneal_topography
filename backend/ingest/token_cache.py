"""Optional on-disk cache of recognition tokens, to try rule changes without re-running OCR."""

import json
from collections.abc import Sequence
from pathlib import Path

from ingest.engines import Recogniser
from ingest.rules import RawToken


def with_cache(recognise: Recogniser, cache_path: Path, dataset_dir: Path) -> Recogniser:
    """Use the cache file when it covers every image; otherwise recognise and write it."""

    def cached(images: Sequence[Path]) -> dict[Path, list[list[RawToken]]]:
        if cache_path.is_file():
            stored = json.loads(cache_path.read_text(encoding="utf-8"))
            keys = {image: str(image.relative_to(dataset_dir)) for image in images}
            if all(key in stored for key in keys.values()):
                return {
                    image: [[RawToken(*token) for token in tokens] for tokens in stored[key]]
                    for image, key in keys.items()
                }
        result = recognise(images)
        payload = {
            str(image.relative_to(dataset_dir)): [
                [[t.text, t.confidence, t.x, t.y] for t in tokens] for tokens in passes
            ]
            for image, passes in result.items()
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return result

    return cached
