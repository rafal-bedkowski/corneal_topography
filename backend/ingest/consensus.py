"""Combine the tokens of several recognition passes into one list of extracted values.

Tokens that lie close together describe the same printed text. Within such a cluster the value
that most passes agree on wins; `confidence` is the share of passes that read it.
"""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.constants import MapType
from app.models import ExtractedValue
from ingest.rules import MIN_CONFIDENCE, RawToken, classify

CLUSTER_RADIUS = 0.03  # fraction of the image size


@dataclass
class _Cluster:
    x: float
    y: float
    members: list[tuple[int, RawToken]] = field(default_factory=list)

    def add(self, pass_index: int, token: RawToken) -> None:
        self.members.append((pass_index, token))
        count = len(self.members)
        self.x += (token.x - self.x) / count
        self.y += (token.y - self.y) / count


def merge_passes(passes: Sequence[Sequence[RawToken]], map_type: MapType) -> list[ExtractedValue]:
    total = len(passes)
    if total == 0:
        return []
    clusters: list[_Cluster] = []
    for pass_index, tokens in enumerate(passes):
        for token in tokens:
            cluster = _nearest(clusters, token)
            if cluster is None:
                cluster = _Cluster(token.x, token.y)
                clusters.append(cluster)
            cluster.add(pass_index, token)

    values: list[ExtractedValue] = []
    for cluster in clusters:
        values.extend(_resolve(cluster, map_type, total))
    values.sort(key=lambda value: (value.y, value.x))
    return values


def _nearest(clusters: Sequence[_Cluster], token: RawToken) -> _Cluster | None:
    best: _Cluster | None = None
    best_distance = CLUSTER_RADIUS
    for cluster in clusters:
        distance = math.hypot(cluster.x - token.x, cluster.y - token.y)
        if distance <= best_distance:
            best, best_distance = cluster, distance
    return best


def _resolve(cluster: _Cluster, map_type: MapType, total: int) -> list[ExtractedValue]:
    groups: dict[tuple[str, str | float | None], list[tuple[int, ExtractedValue]]] = defaultdict(
        list
    )
    for pass_index, token in cluster.members:
        value = classify(token, map_type)
        reading = value.value if value.status == "accepted" else value.text
        groups[(value.status, reading)].append((pass_index, value))

    for statuses in (("accepted",), ("low_confidence", "out_of_range")):
        candidates = [group for (status, _), group in groups.items() if status in statuses]
        if candidates:
            best = max(candidates, key=lambda group: (_passes(group), _best_confidence(group)))
            return [_summarise(best, total, cluster)]
    return [group[0][1] for (status, _), group in groups.items() if status == "rejected"]


def _passes(group: Sequence[tuple[int, ExtractedValue]]) -> int:
    return len({pass_index for pass_index, _ in group})


def _best_confidence(group: Sequence[tuple[int, ExtractedValue]]) -> float:
    return max(value.confidence for _, value in group)


def _summarise(
    group: Sequence[tuple[int, ExtractedValue]], total: int, cluster: _Cluster
) -> ExtractedValue:
    best = max((value for _, value in group), key=lambda value: value.confidence)
    agreement = _passes(group) / total
    status = best.status
    if status == "accepted" and agreement < MIN_CONFIDENCE:
        status = "low_confidence"
    return best.model_copy(
        update={"confidence": agreement, "status": status, "x": cluster.x, "y": cluster.y}
    )
