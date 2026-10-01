import numpy as np
import pytest

from sentinel.geolocate import GeoObject
from sentinel.heatmap import density_grid, heatmap_rgb


def _obj(east, north):
    return GeoObject(18.5, 73.8, east, north, (0, 0, 10, 10), 0.9)


def test_density_grid_shape_and_counts():
    objs = [_obj(0.0, 0.0), _obj(5.0, 5.0), _obj(-200.0, 200.0)]
    grid = density_grid(objs, extent_m=220.0, resolution=22)
    assert grid.shape == (22, 22)
    assert grid.sum() == 3


def test_objects_outside_extent_are_dropped():
    grid = density_grid([_obj(1000.0, 0.0)], extent_m=100.0, resolution=10)
    assert grid.sum() == 0


def test_empty_grid():
    grid = density_grid([], extent_m=100.0, resolution=8)
    assert grid.shape == (8, 8) and grid.sum() == 0


def test_heatmap_rgb_shapes():
    grid = density_grid([_obj(0.0, 0.0)], extent_m=100.0, resolution=8)
    img = heatmap_rgb(grid)
    assert img.shape == (8, 8, 3)
    empty = heatmap_rgb(np.zeros((8, 8), np.float32))
    assert empty.shape == (8, 8, 3)


def test_bad_resolution():
    with pytest.raises(ValueError):
        density_grid([], extent_m=100.0, resolution=0)
