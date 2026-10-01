import numpy as np

from sentinel.camera import GroundCamera, Intrinsics, Pose
from sentinel.detect import Detection
from sentinel.geo import enu_to_latlon
from sentinel.geolocate import geolocate, match_errors, to_geojson


def _cam():
    intr = Intrinsics.from_hfov(640, 480, 70.0)
    pose = Pose(18.5204, 73.8567, 120.0, 0.0, 25.0, 0.0)
    return GroundCamera(intr, pose), pose


def test_geolocate_matches_known_ground_point():
    cam, pose = _cam()
    px = cam.ground_to_pixel(30.0, 150.0)
    assert px is not None
    det = Detection((px[0] - 5, px[1] - 5, px[0] + 5, px[1] + 5), 0.9)
    objs = geolocate([det], cam, pose, reference="center")
    assert len(objs) == 1
    lat, lon = enu_to_latlon(30.0, 150.0, pose.lat, pose.lon)
    assert abs(objs[0].lat - lat) < 1e-6
    assert abs(objs[0].lon - lon) < 1e-6
    assert abs(objs[0].range_m - np.hypot(30.0, 150.0)) < 1e-6


def test_detection_above_horizon_is_skipped():
    cam, pose = _cam()
    det = Detection((300, 0, 320, 5), 0.9)   # up in the sky
    assert geolocate([det], cam, pose) == []


def test_geojson_structure():
    cam, pose = _cam()
    px = cam.ground_to_pixel(0.0, 160.0)
    det = Detection((px[0] - 4, px[1] - 4, px[0] + 4, px[1] + 4), 0.8)
    gj = to_geojson(geolocate([det], cam, pose))
    assert gj["type"] == "FeatureCollection"
    assert gj["features"][0]["geometry"]["type"] == "Point"
    lon, lat = gj["features"][0]["geometry"]["coordinates"]
    assert 73.0 < lon < 74.0 and 18.0 < lat < 19.0


def test_match_errors_counts_matches():
    cam, pose = _cam()
    dets = []
    truth = []
    for x, y in [(0.0, 120.0), (20.0, 180.0), (-15.0, 210.0)]:
        px = cam.ground_to_pixel(x, y)
        dets.append(Detection((px[0] - 4, px[1] - 4, px[0] + 4, px[1] + 4), 0.9))
        truth.append(enu_to_latlon(x, y, pose.lat, pose.lon))
    objs = geolocate(dets, cam, pose)
    errors, matched = match_errors(objs, truth, max_match_m=5.0)
    assert matched == 3
    assert all(e < 1e-3 for e in errors)
