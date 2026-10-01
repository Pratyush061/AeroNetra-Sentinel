
import numpy as np

from sentinel.camera import (
    GroundCamera,
    Intrinsics,
    Pose,
    attitude_from_normal,
    camera_axes,
    normal_from_horizon,
    rotation_wc,
)


def _cam(heading=0.0, depression=60.0, roll=0.0, alt=120.0, w=640, h=480):
    return GroundCamera(Intrinsics.from_hfov(w, h, 70.0), Pose(18.5, 73.8, alt, heading, depression, roll))


def test_intrinsics_K_roundtrip():
    intr = Intrinsics.from_hfov(640, 480, 70.0)
    assert np.allclose(intr.K @ intr.K_inv, np.eye(3))


def test_rotation_is_orthonormal():
    for hd, dep, rl in [(0, 60, 0), (90, 45, 20), (200, 75, -15)]:
        R = rotation_wc(hd, dep, rl)
        assert np.allclose(R.T @ R, np.eye(3), atol=1e-9)
        assert abs(np.linalg.det(R) - 1.0) < 1e-9


def test_nadir_axes():
    r, d, f = camera_axes(0.0, 90.0, 0.0)
    assert np.allclose(f, [0, 0, -1], atol=1e-9)   # looking straight down
    assert np.allclose(r, [1, 0, 0], atol=1e-9)    # image right = east
    assert np.allclose(d, [0, -1, 0], atol=1e-9)   # image down = south


def test_pixel_ground_roundtrip():
    cam = _cam()
    for x, y in [(30.0, 40.0), (-50.0, 80.0), (120.0, -30.0), (0.0, 0.0)]:
        px = cam.ground_to_pixel(x, y)
        assert px is not None
        back = cam.pixel_to_ground(*px)
        assert back is not None
        assert abs(back[0] - x) < 1e-6
        assert abs(back[1] - y) < 1e-6


def test_ground_point_is_east_and_north_correctly():
    cam = _cam(heading=0.0, depression=60.0)
    # a point straight ahead (north) should project near the principal point column
    px = cam.ground_to_pixel(0.0, 200.0)
    assert px is not None
    assert abs(px[0] - cam.K[0, 2]) < 2.0
    # a point to the east should be to the right in the image
    px_east = cam.ground_to_pixel(200.0, 0.0)
    assert px_east is not None and px_east[0] > cam.K[0, 2]


def test_horizon_is_above_ground_points():
    cam = _cam(depression=25.0)
    a, b, c = cam.horizon_line()
    cx, cy = cam.K[0, 2], cam.K[1, 2]
    v_h = -(a * cx + c) / b
    assert 0.0 < v_h < cy                                   # horizon visible near the top
    assert cam.pixel_to_ground(cx, cy) is not None          # below -> ground
    assert cam.pixel_to_ground(cx, v_h - 20.0) is None      # above -> sky


def test_attitude_roundtrip_from_normal():
    for hd in [0.0, 90.0, 210.0]:
        for dep in [30.0, 45.0, 60.0, 75.0]:
            for rl in [-25.0, 0.0, 25.0]:
                cam = _cam(hd, dep, rl)
                n = cam.ground_normal_cam()
                dep_hat, roll_hat = attitude_from_normal(n)
                assert abs(dep_hat - dep) < 1e-6
                assert abs(((roll_hat - rl + 180) % 360) - 180) < 1e-6


def test_normal_from_horizon_matches():
    cam = _cam(45.0, 55.0, 10.0)
    line = cam.horizon_line()
    n = normal_from_horizon(line, cam.K)
    assert np.allclose(n, cam.ground_normal_cam(), atol=1e-6)
