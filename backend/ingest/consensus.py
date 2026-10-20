"""Combine the tokens of several recognition passes into one list of extracted values.

Tokens that lie close together describe the same printed text. Within such a cluster the value
that most passes agree on wins; `confidence` is the share of passes that read it.
"""

import math
import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.constants import MapType
from app.models import ExtractedValue
from ingest.rules import RawToken, classify

CLUSTER_RADIUS = 0.03  # fraction of the image size
MIN_VOTES = 2  # passes that must read a value for it to stay `accepted`
NEIGHBOUR_RADIUS = 0.15  # fraction of the image size, for breaking ties between readings

Group = list[tuple[int, ExtractedValue]]


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

    groups_by_cluster = [(cluster, _groups(cluster, map_type)) for cluster in clusters]
    settled = [
        _summarise(_best(groups), total, cluster)
        for cluster, groups in groups_by_cluster
        if _is_decided(groups)
    ]
    values: list[ExtractedValue] = []
    for cluster, groups in groups_by_cluster:
        if not groups:
            continue
        if groups[0][0][1].status == "rejected":
            values.extend(group[0][1] for group in groups)
            continue
        if _is_decided(groups):
            values.append(_summarise(_best(groups), total, cluster))
            continue
        values.append(_summarise(_break_tie(groups, cluster, settled), total, cluster))
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


def _groups(cluster: _Cluster, map_type: MapType) -> list[Group]:
    """Group the readings of a cluster; the groups of the best status class come first."""
    grouped: dict[tuple[str, str | float | None], Group] = defaultdict(list)
    for pass_index, token in cluster.members:
        value = classify(token, map_type)
        reading = value.value if value.status == "accepted" else value.text
        grouped[(value.status, reading)].append((pass_index, value))
    for statuses in (("accepted",), ("low_confidence", "out_of_range")):
        candidates = [group for (status, _), group in grouped.items() if status in statuses]
        if candidates:
            return candidates
    return [group for (status, _), group in grouped.items() if status == "rejected"]


def _rank(group: Group) -> tuple[int, float]:
    return (_passes(group), _best_confidence(group))


def _best(groups: Sequence[Group]) -> Group:
    return max(groups, key=_rank)


def _is_decided(groups: Sequence[Group]) -> bool:
    """Whether the cluster has a single leading reading."""
    if groups[0][0][1].status == "rejected":
        return True
    ranked = sorted((_passes(group) for group in groups), reverse=True)
    return len(ranked) == 1 or ranked[0] > ranked[1]


def _break_tie(
    groups: Sequence[Group], cluster: _Cluster, settled: Sequence[ExtractedValue]
) -> Group:
    """Among readings with equal votes, prefer the one closest to its settled neighbours."""
    leaders = [group for group in groups if _passes(group) == max(_passes(g) for g in groups)]
    neighbours = [
        value.value
        for value in settled
        if value.status == "accepted"
        and value.value is not None
        and math.hypot(value.x - cluster.x, value.y - cluster.y) <= NEIGHBOUR_RADIUS
    ]
    if len(neighbours) >= 3 and all(group[0][1].value is not None for group in leaders):
        median = statistics.median(neighbours)
        return min(
            leaders,
            key=lambda group: (abs((group[0][1].value or 0.0) - median), -_best_confidence(group)),
        )
    return max(leaders, key=_best_confidence)


def _passes(group: Group) -> int:
    return len({pass_index for pass_index, _ in group})


def _best_confidence(group: Group) -> float:
    return max(value.confidence for _, value in group)


def _summarise(group: Group, total: int, cluster: _Cluster) -> ExtractedValue:
    best = max((value for _, value in group), key=lambda value: value.confidence)
    votes = _passes(group)
    agreement = votes / total
    status = best.status
    if status == "accepted" and votes < min(MIN_VOTES, total):
        status = "low_confidence"
    return best.model_copy(
        update={"confidence": agreement, "status": status, "x": cluster.x, "y": cluster.y}
    )
