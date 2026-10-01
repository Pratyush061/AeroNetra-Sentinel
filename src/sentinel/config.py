"""Typed configuration for AeroNetra-Sentinel (nested dataclasses + YAML)."""

from __future__ import annotations

import dataclasses
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SceneConfig:
    """Synthetic georeferenced scene parameters."""

    width: int = 640
    height: int = 480
    hfov: float = 70.0
    lat0: float = 18.5204          # drone ground position (Pune)
    lon0: float = 73.8567
    altitude: float = 120.0        # metres above ground
    heading: float = 0.0           # compass degrees
    depression: float = 25.0       # degrees below the horizon
    roll: float = 0.0
    num_objects: int = 8
    seed: int = 3


@dataclass
class DetectConfig:
    """Object detection parameters."""

    blur_kernel: int = 31
    diff_threshold: int = 18
    min_area: int = 25
    morph_kernel: int = 3
    max_area_frac: float = 0.20


@dataclass
class HorizonConfig:
    """Self-calibrating horizon estimation parameters."""

    tau: float = 3.0               # RANSAC inlier band, pixels
    min_columns: int = 30          # minimum usable image columns
    min_inliers: int = 20          # minimum RANSAC inliers
    iterations: int = 200


@dataclass
class SentinelConfig:
    """Top-level configuration."""

    scene: SceneConfig = field(default_factory=SceneConfig)
    detect: DetectConfig = field(default_factory=DetectConfig)
    horizon: HorizonConfig = field(default_factory=HorizonConfig)
    attitude_source: str = "estimated"   # "estimated" | "true"
    reference: str = "center"            # detection reference point: center|bottom
    output_dir: str = "outputs"
    save_heatmap: bool = True
    heatmap_extent: float = 220.0        # metres
    heatmap_resolution: int = 32


def _build(cls: type, data: dict[str, Any] | None):
    data = data or {}
    hints = typing.get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(cls):
        if f.name not in data:
            continue
        target = hints[f.name]
        value = data[f.name]
        if dataclasses.is_dataclass(target) and isinstance(value, dict):
            value = _build(target, value)
        kwargs[f.name] = value
    return cls(**kwargs)


def config_from_dict(data: dict[str, Any]) -> SentinelConfig:
    return _build(SentinelConfig, data)


def load_config(path: str | Path | None = None) -> SentinelConfig:
    if path is None:
        return SentinelConfig()
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a mapping, got {type(data).__name__}")
    return config_from_dict(data)


def to_dict(cfg: SentinelConfig) -> dict[str, Any]:
    return dataclasses.asdict(cfg)
