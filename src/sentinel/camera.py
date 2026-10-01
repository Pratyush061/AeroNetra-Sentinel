"""Pinhole camera geometry and single-frame monocular ground-plane registration.

OpenCV camera convention: x right, y down, z forward. A UAV pose is a ground
position, an altitude, and an attitude expressed as heading (compass), depression
(angle below the horizon) and roll.

Given intrinsics, attitude and altitude, the mapping from an image pixel to the
ground plane Z=0 is a **homography**. That single fact is the basis of this
project: no stereo, no LiDAR -- one frame plus the UAV's own altitude.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Intrinsics:
    """Pinhole intrinsics."""

    fx: float
    fy: float
    cx: float
    cy: float

    @property
    def K(self) -> np.ndarray:
        return np.array([[self.fx, 0.0, self.cx],
                         [0.0, self.fy, self.cy],
                         [0.0, 0.0, 1.0]])

    @property
    def K_inv(self) -> np.ndarray:
        return np.linalg.inv(self.K)

    @staticmethod
    def from_hfov(width: int, height: int, hfov_deg: float) -> "Intrinsics":
        """Build intrinsics from a horizontal field of view."""
        fx = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        return Intrinsics(fx=fx, fy=fx, cx=width / 2.0, cy=height / 2.0)


@dataclass
class Pose:
    """UAV ground position, altitude and attitude."""

    lat: float
    lon: float
    altitude: float           # metres above the ground plane
    heading: float = 0.0      # compass degrees (0 = north, 90 = east)
    depression: float = 60.0  # degrees below the horizon (90 = nadir)
    roll: float = 0.0         # degrees about the optical axis


def camera_axes(heading_deg: float, depression_deg: float, roll_deg: float):
    """Return the camera (right, down, forward) unit axes in the world ENU frame."""
    hd = math.radians(heading_deg)
    dep = math.radians(depression_deg)
    rl = math.radians(roll_deg)

    forward = np.array([math.cos(dep) * math.sin(hd),
                        math.cos(dep) * math.cos(hd),
                        -math.sin(dep)])
    right0 = np.array([math.cos(hd), -math.sin(hd), 0.0])
    down0 = np.cross(forward, right0)

    c, s = math.cos(rl), math.sin(rl)
    right = right0 * c + np.cross(forward, right0) * s
    down = down0 * c + np.cross(forward, down0) * s
    return right, down, forward


def rotation_wc(heading_deg: float, depression_deg: float, roll_deg: float) -> np.ndarray:
    """Camera-to-world rotation (columns are right, down, forward)."""
    right, down, forward = camera_axes(heading_deg, depression_deg, roll_deg)
    return np.column_stack([right, down, forward])


class GroundCamera:
    """A calibrated camera looking at a flat ground plane."""

    def __init__(self, intrinsics: Intrinsics, pose: Pose):
        self.K = intrinsics.K
        self.K_inv = intrinsics.K_inv
        self.pose = pose
        self.R_wc = rotation_wc(pose.heading, pose.depression, pose.roll)
        self.position = np.array([0.0, 0.0, pose.altitude])
        self._M = self.R_wc @ self.K_inv

    def ray_world(self, u: float, v: float) -> np.ndarray:
        """Unit world direction of the ray through pixel (u, v)."""
        d = self._M @ np.array([u, v, 1.0])
        n = float(np.linalg.norm(d))
        return d / n if n > 0 else d

    def ground_homography(self) -> np.ndarray:
        """3x3 homography mapping an image pixel to the ground plane (Z=0)."""
        alt = self.pose.altitude
        m = self._M
        return np.array([
            [-alt * m[0, 0], -alt * m[0, 1], -alt * m[0, 2]],
            [-alt * m[1, 0], -alt * m[1, 1], -alt * m[1, 2]],
            [m[2, 0], m[2, 1], m[2, 2]],
        ])

    def pixel_to_ground(self, u: float, v: float):
        """Image pixel -> ground (east, north) metres, or ``None`` above the horizon.

        The homogeneous denominator is the ray's world up-component, which is
        negative for any ray that meets the ground plane.
        """
        q = self.ground_homography() @ np.array([u, v, 1.0])
        if q[2] >= -1e-9:
            return None
        return (float(q[0] / q[2]), float(q[1] / q[2]))

    def ground_to_pixel(self, x: float, y: float):
        """Ground (east, north) metres -> image pixel, or ``None`` if behind the camera."""
        v_cam = self.R_wc.T @ np.array([x, y, -self.pose.altitude])
        if v_cam[2] <= 1e-9:
            return None
        p = self.K @ v_cam
        return (float(p[0] / p[2]), float(p[1] / p[2]))

    def ground_normal_cam(self) -> np.ndarray:
        """Unit ground-plane normal expressed in camera coordinates."""
        n = self.R_wc.T @ np.array([0.0, 0.0, 1.0])
        return n / float(np.linalg.norm(n))

    def horizon_line(self) -> np.ndarray:
        """Vanishing line of the ground plane as ``(a, b, c)`` with a*u + b*v + c = 0.

        For a plane with camera-frame normal ``n`` the vanishing line is
        ``l = K^-T n``; a pixel ``p`` lies on it iff ``n . (K^-1 p) = 0``.
        """
        line = self.K_inv.T @ self.ground_normal_cam()
        n2 = float(np.linalg.norm(line[:2]))
        return line / n2 if n2 > 1e-12 else line


def normal_from_horizon(line, K: np.ndarray) -> np.ndarray:
    """Recover the unit ground normal (camera frame) from a horizon line."""
    n = K.T @ np.asarray(line, float)
    return n / float(np.linalg.norm(n))


def attitude_from_normal(n_cam) -> tuple[float, float]:
    """Recover ``(depression_deg, roll_deg)`` from the ground normal in camera coords.

    Roll is only observable when the camera is not exactly nadir, which is
    physically correct: looking straight down, rotation about the optical axis
    is invisible.
    """
    n = np.asarray(n_cam, float)
    n = n / float(np.linalg.norm(n))
    cos_theta = float(np.clip(n[2], -1.0, 1.0))
    depression = math.degrees(math.acos(cos_theta)) - 90.0
    roll = math.degrees(math.atan2(-n[0], -n[1]))
    return depression, roll
