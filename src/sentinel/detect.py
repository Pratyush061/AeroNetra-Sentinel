"""Object detection for a single frame.

A local-contrast detector: objects stand out from their immediate surround, so
comparing the frame with a heavily blurred version of itself and thresholding
isolates them without any training. (A learned detector can be dropped in later;
the output contract is a list of boxes.)
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import DetectConfig


@dataclass
class Detection:
    """A detection in xyxy image coordinates."""

    box: tuple[float, float, float, float]
    score: float
    label: str = "object"

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.box
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def reference_point(self, mode: str = "center") -> tuple[float, float]:
        x1, y1, x2, y2 = self.box
        if mode == "bottom":
            return ((x1 + x2) / 2.0, y2)
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def detect_objects(bgr: np.ndarray, cfg: DetectConfig) -> list[Detection]:
    """Detect high-contrast objects against the ground texture.

    Kernel and area thresholds scale with the frame so detection behaves the
    same at any resolution.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    h, w = gray.shape[:2]
    scale = max(0.15, (h * w) / (640.0 * 480.0))

    k = max(3, int(cfg.blur_kernel) | 1)
    k = min(k, max(3, (min(h, w) // 8) | 1))
    background = cv2.medianBlur(gray, k)
    diff = cv2.absdiff(gray, background)
    mask = (diff >= cfg.diff_threshold).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, cfg.morph_kernel),) * 2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    min_area = max(4, int(cfg.min_area * scale))
    max_area = cfg.max_area_frac * h * w
    detections: list[Detection] = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        bw = int(stats[i, cv2.CC_STAT_WIDTH])
        bh = int(stats[i, cv2.CC_STAT_HEIGHT])
        score = float(min(1.0, area / (min_area * 8.0)))
        detections.append(Detection((x, y, x + bw, y + bh), score, "object"))
    return detections
