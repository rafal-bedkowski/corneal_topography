from dataclasses import dataclass
from typing import Final, Literal

Split = Literal["train_validation", "independent_test"]
Label = Literal["normal", "keratoconus", "suspect"]
MapType = Literal["sag_a", "sag_p", "elv_a", "elv_p", "ec_a", "ec_p", "ct_a"]
Laterality = Literal["OD", "OS", "unknown"]
ValueStatus = Literal["accepted", "low_confidence", "out_of_range", "rejected"]
ExclusionReason = Literal["duplicate", "duplicate_conflicting_labels"]

SPLITS: Final[tuple[Split, ...]] = ("train_validation", "independent_test")
LABELS: Final[tuple[Label, ...]] = ("normal", "keratoconus", "suspect")
LATERALITIES: Final[tuple[Laterality, ...]] = ("OD", "OS", "unknown")
VALUE_STATUSES: Final[tuple[ValueStatus, ...]] = (
    "accepted",
    "low_confidence",
    "out_of_range",
    "rejected",
)

# Folder names (the dataset repeats each name on two nested levels).
SPLIT_DIRS: Final[dict[Split, str]] = {
    "train_validation": "Train_Validation sets",
    "independent_test": "Independent Test Set",
}
LABEL_DIRS: Final[dict[Label, str]] = {
    "normal": "Normal",
    "keratoconus": "Keratoconus",
    "suspect": "Suspect",
}
LABEL_PREFIXES: Final[dict[Label, str]] = {
    "normal": "NOR",
    "keratoconus": "KCN",
    "suspect": "SUSP",
}


@dataclass(frozen=True)
class MapSpec:
    map_type: MapType
    file_suffix: str
    title: str
    unit: str


MAP_SPECS: Final[tuple[MapSpec, ...]] = (
    MapSpec("sag_a", "Sag_A", "Axial curvature, anterior", "D"),
    MapSpec("sag_p", "Sag_P", "Axial curvature, posterior", "D"),
    MapSpec("elv_a", "Elv_A", "Elevation, anterior", "µm"),
    MapSpec("elv_p", "Elv_P", "Elevation, posterior", "µm"),
    MapSpec("ec_a", "EC_A", "Elevation (alt. reference), anterior", "µm"),
    MapSpec("ec_p", "EC_P", "Elevation (alt. reference), posterior", "µm"),
    MapSpec("ct_a", "CT_A", "Corneal thickness", "µm"),
)
MAP_SPEC_BY_TYPE: Final[dict[str, MapSpec]] = {spec.map_type: spec for spec in MAP_SPECS}

INDEX_VERSION: Final = 1
