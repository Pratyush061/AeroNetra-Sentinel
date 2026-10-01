"""Dataset adapters for geo-registration.

Geo-registration needs data that carries **geographic** metadata: the camera
pose and the ground truth in coordinates. This registry marks which aerial and
satellite datasets are geo-tagged, and ships pure parsers so the loaders are
unit-testable without the data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    name: str
    modality: str
    geotagged: bool
    url: str
    note: str


_REGISTRY: dict[str, DatasetSpec] = {
    "auair": DatasetSpec(
        "auair", "AU-AIR", "low-altitude UAV RGB + flight logs", True,
        "https://bozcani.github.io/auairdataset",
        "UAV imagery with GPS/IMU flight logs -- directly usable for geo-registration.",
    ),
    "seadronessee": DatasetSpec(
        "seadronessee", "SeaDronesSee", "maritime UAV RGB", True,
        "https://seadronessee.cs.uni-tuebingen.de/",
        "Geo-referenced maritime UAV data; small-object detection.",
    ),
    "uavdt": DatasetSpec(
        "uavdt", "UAVDT", "aerial RGB video", True,
        "https://sites.google.com/view/uavdt-dataset",
        "UAV detection/tracking; sequences carry flight metadata.",
    ),
    "uavid": DatasetSpec(
        "uavid", "UAVid", "aerial semantic video", True,
        "https://uavid.nl/",
        "Aerial semantic segmentation with recording metadata.",
    ),
    "mars": DatasetSpec(
        "mars", "MARS", "multi-agent UAV tracking", True,
        "https://github.com/sail-sg/MARS",
        "Multi-agent UAV trajectories with world coordinates.",
    ),
    "dota": DatasetSpec(
        "dota", "DOTA", "aerial oriented boxes", True,
        "https://captain-whu.github.io/DOTA/",
        "Large aerial oriented-object benchmark; geo-referenced tiles.",
    ),
    "spacenet": DatasetSpec(
        "spacenet", "SpaceNet", "satellite imagery", True,
        "https://spacenet.ai/datasets/",
        "Satellite imagery with building footprints in coordinates.",
    ),
    "xbd": DatasetSpec(
        "xbd", "xBD", "satellite before/after", True,
        "https://xview2.org/",
        "Satellite damage assessment with geo-located labels.",
    ),
    "visdrone": DatasetSpec(
        "visdrone", "VisDrone", "aerial RGB detection/tracking", False,
        "https://github.com/VisDrone/VisDrone-Dataset",
        "Widely used aerial benchmark; no per-frame GPS -- one option among many.",
    ),
}


def list_datasets() -> list[DatasetSpec]:
    return list(_REGISTRY.values())


def geotagged_datasets() -> list[DatasetSpec]:
    return [d for d in _REGISTRY.values() if d.geotagged]


def get_dataset(key: str) -> DatasetSpec:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown dataset {key!r}. Known: {', '.join(sorted(_REGISTRY))}")
    return _REGISTRY[key]


def dataset_dir(key: str, root: str | Path = "data") -> Path:
    return Path(root) / key


def is_available(key: str, root: str | Path = "data") -> bool:
    d = dataset_dir(key, root)
    return d.is_dir() and any(d.iterdir())


def require(key: str, root: str | Path = "data") -> Path:
    spec = get_dataset(key)
    d = dataset_dir(key, root)
    if not is_available(key, root):
        raise FileNotFoundError(
            f"Dataset '{spec.name}' not found at {d}.\n"
            f"  Download: {spec.url}\n"
            f"  Then place the extracted files under {d}.\n"
            f"  ({spec.note})"
        )
    return d


def parse_flight_log(path: str | Path) -> dict:
    """Parse a simple JSON flight log: lat, lon, altitude, heading, depression, roll."""
    data = json.loads(Path(path).read_text())
    required = {"lat", "lon", "altitude"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"Flight log missing keys {sorted(missing)}; found {sorted(data)}")
    return {
        "lat": float(data["lat"]),
        "lon": float(data["lon"]),
        "altitude": float(data["altitude"]),
        "heading": float(data.get("heading", 0.0)),
        "depression": float(data.get("depression", 60.0)),
        "roll": float(data.get("roll", 0.0)),
    }
