"""Geospatial density heatmap of geolocated objects."""

from __future__ import annotations

import numpy as np

from .geolocate import GeoObject


def density_grid(
    objects: list[GeoObject],
    extent_m: float = 220.0,
    resolution: int = 32,
) -> np.ndarray:
    """Count geolocated objects per cell of a metric grid centred on the UAV.

    The grid spans ``[-extent_m, extent_m]`` in both east and north; cell
    ``[row, col]`` counts objects, with row 0 at the far (north) edge.
    """
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    grid = np.zeros((resolution, resolution), np.float32)
    if not objects:
        return grid
    size = 2.0 * extent_m / resolution
    for obj in objects:
        col = int((obj.east + extent_m) / size)
        row = int((extent_m - obj.north) / size)
        if 0 <= row < resolution and 0 <= col < resolution:
            grid[row, col] += 1.0
    return grid


def heatmap_rgb(grid: np.ndarray) -> np.ndarray:
    """Render a density grid as an RGB image via a colormap."""
    if grid.size == 0 or float(grid.max()) <= 0:
        return np.zeros((*grid.shape, 3), np.uint8)
    normalized = (grid / float(grid.max()) * 255.0).astype(np.uint8)
    import cv2

    return cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
