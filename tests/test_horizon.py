import numpy as np

from sentinel.config import HorizonConfig, SceneConfig
from sentinel.horizon import estimate_attitude, estimate_horizon
from sentinel.scene import GeoScene


def test_attitude_recovered_when_horizon_visible():
    cfg = SceneConfig(depression=25.0, roll=0.0)
    scene = GeoScene(cfg)
    frame = scene.render()
    est = estimate_attitude(frame.gray, scene.intrinsics.K, HorizonConfig(), seed=0)
    assert est is not None
    depression, roll, ratio = est
    assert abs(depression - 25.0) < 2.0
    assert abs(roll) < 2.0
    assert ratio > 0.5


def test_roll_recovered():
    cfg = SceneConfig(depression=22.0, roll=8.0)
    scene = GeoScene(cfg)
    frame = scene.render()
    est = estimate_attitude(frame.gray, scene.intrinsics.K, HorizonConfig(), seed=0)
    assert est is not None
    assert abs(est[1] - 8.0) < 3.0


def test_no_horizon_returns_none_when_looking_down():
    # At high depression the horizon is above the frame; nothing to estimate.
    cfg = SceneConfig(depression=60.0)
    scene = GeoScene(cfg)
    frame = scene.render()
    assert estimate_horizon(frame.gray, HorizonConfig(), seed=0) is None
    assert estimate_attitude(frame.gray, scene.intrinsics.K, HorizonConfig(), seed=0) is None


def test_horizon_line_shape():
    cfg = SceneConfig(depression=25.0)
    scene = GeoScene(cfg)
    line, ratio = estimate_horizon(scene.render().gray, HorizonConfig(), seed=0)
    assert line.shape == (3,)
    assert abs(np.linalg.norm(line[:2]) - 1.0) < 1e-6
