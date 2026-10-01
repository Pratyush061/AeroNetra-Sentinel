"""Visualisation helpers (OpenCV drawing only)."""

from __future__ import annotations

import cv2
import numpy as np

from .detect import Detection
from .geolocate import GeoObject


def draw_detections(img: np.ndarray, detections: list[Detection], color=(0, 200, 255)) -> None:
    for det in detections:
        x1, y1, x2, y2 = (int(v) for v in det.box)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)


def draw_geo_labels(img: np.ndarray, objects: list[GeoObject]) -> None:
    for obj in objects:
        x1, y1, x2, y2 = (int(v) for v in obj.box)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{obj.lat:.5f},{obj.lon:.5f}"
        cv2.putText(img, label, (x1, max(10, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, label, (x1, max(10, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (255, 255, 255), 1, cv2.LINE_AA)


def draw_horizon(img: np.ndarray, line, color=(255, 0, 255)) -> None:
    """Draw a line ``(a, b, c)`` with a*u + b*v + c = 0."""
    if line is None:
        return
    a, b, c = (float(v) for v in line)
    h, w = img.shape[:2]
    if abs(b) >= abs(a):
        if abs(b) < 1e-9:
            return
        pts = [(0, int(-c / b)), (w - 1, int(-(a * (w - 1) + c) / b))]
    else:
        pts = [(int(-c / a), 0), (int(-(b * (h - 1) + c) / a), h - 1)]
    cv2.line(img, pts[0], pts[1], color, 2, cv2.LINE_AA)


def draw_hud(img: np.ndarray, lines: list[str]) -> None:
    y = 22
    for text in lines:
        cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        y += 20


def annotate(
    rgb: np.ndarray,
    detections: list[Detection],
    objects: list[GeoObject],
    horizon_line=None,
    hud: list[str] | None = None,
) -> np.ndarray:
    img = np.ascontiguousarray(rgb.copy())
    draw_horizon(img, horizon_line)
    draw_detections(img, detections)
    draw_geo_labels(img, objects)
    if hud:
        draw_hud(img, hud)
    return img
