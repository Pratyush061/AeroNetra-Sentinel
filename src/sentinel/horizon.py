"""Self-calibrating horizon estimation.

Sky and ground differ in texture, so the horizon is the boundary that best
separates them. We find, per image column, the row where the cumulative edge
energy crosses half of the column total, then fit a line to those candidates
with RANSAC. From the line and the intrinsics we recover the ground-plane
normal -- hence roll and depression -- with no calibration target and no IMU.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from .camera import attitude_from_normal, normal_from_horizon
from .config import HorizonConfig


def edge_magnitude(gray: np.ndarray) -> np.ndarray:
    """Sobel gradient magnitude of a grayscale image."""
    g = np.asarray(gray, np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return np.sqrt(gx * gx + gy * gy)


def column_transition_rows(gray: np.ndarray, mag: np.ndarray | None = None) -> np.ndarray:
    """Per-column onset of texture (the sky->ground boundary), as (x, y) pairs.

    The sky is smooth and the ground is textured, so the horizon is where each
    column's smoothed edge energy first rises above a fraction of its peak.
    """
    mag = edge_magnitude(gray) if mag is None else mag

    window = np.ones(9) / 9.0
    smoothed = np.apply_along_axis(lambda c: np.convolve(c, window, mode="same"), 0, mag)

    height = mag.shape[0]
    cands = []
    for x in range(mag.shape[1]):
        col = smoothed[:, x]
        peak = float(col.max())
        if peak < 5.0:                      # essentially textureless column
            continue
        threshold = 0.35 * peak
        above = col > threshold
        if not above.any():
            continue
        y = int(np.argmax(above))
        # The region below the candidate must be clearly more textured than the
        # region above, otherwise this column has no visible horizon.
        top = float(mag[:y].mean()) if y > 0 else 0.0
        bottom = float(mag[y:].mean())
        if bottom < 3.0 or bottom < 2.0 * max(top, 1e-6):
            continue
        cands.append((x, min(y, height - 1)))
    return np.asarray(cands, np.float32).reshape(-1, 2)


def fit_line_ransac(points: np.ndarray, cfg: HorizonConfig, seed: int = 0):
    """Robustly fit ``v = m*u + k``; return ``(line_abc, inlier_ratio)`` or None."""
    if len(points) < cfg.min_columns:
        return None
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(cfg.iterations):
        i, j = rng.choice(len(points), 2, replace=False)
        (x1, y1), (x2, y2) = points[i], points[j]
        if abs(x2 - x1) < 1e-6:
            continue
        m = (y2 - y1) / (x2 - x1)
        k = y1 - m * x1
        dist = np.abs(points[:, 1] - (m * points[:, 0] + k))
        inliers = dist < cfg.tau
        count = int(inliers.sum())
        if best is None or count > best[0]:
            best = (count, inliers)
    if best is None or best[0] < cfg.min_inliers:
        return None

    inl = best[1]
    p = points[inl]
    design = np.stack([p[:, 0], np.ones(len(p))], axis=1)
    sol, *_ = np.linalg.lstsq(design, p[:, 1], rcond=None)
    m, k = float(sol[0]), float(sol[1])
    a, b, c = m, -1.0, k
    norm = math.hypot(a, b)
    return np.array([a / norm, b / norm, c / norm]), best[0] / len(points)


def estimate_horizon(gray: np.ndarray, cfg: HorizonConfig, seed: int = 0):
    """Estimate the horizon line ``(a, b, c)`` and its inlier ratio, or ``None``.

    Returns ``None`` when the frame has no visible sky/ground boundary (for
    example a near-nadir view), rather than inventing one.
    """
    mag = edge_magnitude(gray)
    h = mag.shape[0]
    # Sample only the very top rows: sky is smooth there, while ground is
    # heavily textured (especially near the horizon, where perspective
    # compresses texture). If the top is textured, there is no visible sky.
    band = max(3, h // 48)
    top = float(mag[:band].mean())
    bottom = float(mag[-band:].mean())
    if bottom < 3.0 or top > 0.5 * bottom:
        return None                      # no sky region -> no horizon to find
    points = column_transition_rows(gray, mag)
    return fit_line_ransac(points, cfg, seed=seed)


def estimate_attitude(gray: np.ndarray, K: np.ndarray, cfg: HorizonConfig, seed: int = 0):
    """Recover ``(depression_deg, roll_deg, inlier_ratio)`` from a single image."""
    result = estimate_horizon(gray, cfg, seed=seed)
    if result is None:
        return None
    line, ratio = result
    normal = normal_from_horizon(line, K)
    # The ground normal must point away from the camera's forward axis.
    if normal[2] > 0:
        normal = -normal
    depression, roll = attitude_from_normal(normal)
    return depression, roll, ratio
