"""AeroNetra-Sentinel — single-frame monocular geo-registration for UAVs.

From **one** image, the UAV's own altitude and (optionally) its attitude, the
project recovers the geographic coordinates of every detected object -- no
stereo, no LiDAR, no calibration target. The self-calibrating step recovers
attitude from the horizon line itself.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__", "SentinelConfig", "load_config", "SentinelPipeline"]


def __getattr__(name: str):
    if name in ("SentinelConfig", "load_config", "config_from_dict", "to_dict"):
        from . import config as _config

        return getattr(_config, name)
    if name in ("SentinelPipeline", "run_demo"):
        from . import pipeline as _pipeline

        return getattr(_pipeline, name)
    raise AttributeError(f"module 'sentinel' has no attribute {name!r}")
