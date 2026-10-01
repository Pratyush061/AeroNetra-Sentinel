import numpy as np

from sentinel.config import SceneConfig
from sentinel.geo import enu_to_latlon
from sentinel.scene import GeoScene


def test_render_shapes():
    scene = GeoScene(SceneConfig())
    frame = scene.render()
    assert frame.rgb.shape == (480, 640, 3)
    assert frame.gray.shape == (480, 640)
    assert frame.rgb.dtype == np.uint8
    assert frame.boxes.shape[1] == 4


def test_boxes_inside_frame():
    frame = GeoScene(SceneConfig()).render()
    assert len(frame.boxes) > 0
    for x1, y1, x2, y2 in frame.boxes:
        assert 0 <= x1 < x2 < 640
        assert 0 <= y1 < y2 < 480


def test_object_geolocation_matches_enu():
    cfg = SceneConfig()
    scene = GeoScene(cfg)
    for obj in scene.objects:
        lat, lon = enu_to_latlon(obj.x, obj.y, cfg.lat0, cfg.lon0)
        assert abs(lat - obj.lat) < 1e-9
        assert abs(lon - obj.lon) < 1e-9


def test_render_is_deterministic():
    a = GeoScene(SceneConfig(seed=5)).render()
    b = GeoScene(SceneConfig(seed=5)).render()
    assert np.array_equal(a.rgb, b.rgb)
    assert np.allclose(a.boxes, b.boxes)


def test_horizon_visible_in_scene():
    cfg = SceneConfig(depression=25.0)
    scene = GeoScene(cfg)
    frame = scene.render()
    # sky at the very top, ground well below the horizon
    line = frame.horizon_line
    a, b, c = line
    v_top = -(a * 0 + c) / b if abs(b) > 1e-9 else 0
    assert v_top > 0            # horizon lies inside the frame
    assert frame.gray[0, :].mean() != frame.gray[-1, :].mean()
