"""Ray-cast synthetic georeferenced aerial scene.

A real renderer, not a toy: for every pixel we cast a ray from the UAV, intersect
the ground plane, and sample a procedural ground texture, so the image has a
genuine horizon and correct perspective. Objects are placed at known ground
coordinates, which gives exact ground-truth geographic positions to score the
geolocation against.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .camera import GroundCamera, Intrinsics, Pose
from .config import SceneConfig
from .geo import enu_to_latlon


@dataclass
class SceneObject:
    """A ground object at a known local position and geographic coordinate."""

    x: float
    y: float
    size: float
    label: str
    lat: float
    lon: float


@dataclass
class SceneFrame:
    """One rendered instant of the georeferenced scene."""

    rgb: np.ndarray                 # (H, W, 3) uint8
    gray: np.ndarray                # (H, W) uint8
    objects: list[SceneObject]
    boxes: np.ndarray               # (M, 4) float32 image-space ground truth
    pose: Pose
    intrinsics: Intrinsics
    horizon_line: np.ndarray        # analytic ground-truth horizon


class GeoScene:
    """Deterministic ray-cast scene with ground-truth geolocation."""

    def __init__(self, cfg: SceneConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.intrinsics = Intrinsics.from_hfov(cfg.width, cfg.height, cfg.hfov)
        self.pose = Pose(cfg.lat0, cfg.lon0, cfg.altitude, cfg.heading, cfg.depression, cfg.roll)
        self.camera = GroundCamera(self.intrinsics, self.pose)
        self._precompute_rays()
        self.objects = self._place_objects()

    # ------------------------------------------------------------------ setup
    def _precompute_rays(self) -> None:
        cfg = self.cfg
        uu, vv = np.meshgrid(np.arange(cfg.width, dtype=np.float64),
                             np.arange(cfg.height, dtype=np.float64))
        homo = np.stack([uu, vv, np.ones_like(uu)], axis=0).reshape(3, -1)
        d = self.camera._M @ homo                      # (3, N) world directions
        self._dir = d
        self._dz = d[2]
        norm = np.linalg.norm(d, axis=0)
        self._dir_unit = d / np.where(norm > 0, norm, 1.0)

    def _place_objects(self) -> list[SceneObject]:
        cfg = self.cfg
        objs: list[SceneObject] = []
        n = cfg.num_objects
        # At this altitude/depression the visible ground starts ~95 m ahead, so
        # objects are spread down the flight direction (north) beyond that.
        for i in range(n):
            t = (i + 0.5) / n
            y = 95.0 + t * 150.0
            x = float(self.rng.uniform(-22.0, 22.0))
            size = float(self.rng.uniform(3.5, 6.0))
            lat, lon = enu_to_latlon(x, y, cfg.lat0, cfg.lon0)
            objs.append(SceneObject(x, y, size, "vehicle", lat, lon))
        return objs

    # --------------------------------------------------------------- texture
    def _ground_gray(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        base = 118.0 + 10.0 * np.sin(x / 6.0) * np.cos(y / 7.5) + 6.0 * np.sin((x + y) / 2.5)
        # a north-south road the UAV is flying along
        on_road = np.abs(x) < 6.0
        base = np.where(on_road, base - 14.0, base)
        dash = on_road & (np.abs(x) < 0.5) & (np.mod(y, 12.0) < 6.0)
        base = np.where(dash, 175.0, base)
        return np.clip(base, 0.0, 255.0)

    def _sky_rgb(self) -> np.ndarray:
        elev = np.arcsin(np.clip(self._dir_unit[2], -1.0, 1.0))
        t = np.clip(elev / (math.pi / 2.0), 0.0, 1.0)   # 0 at horizon, 1 at zenith
        bright = 190.0 - 55.0 * t
        r = bright * 0.66
        g = bright * 0.80
        b = np.clip(bright * 1.02, 0, 255)
        return np.stack([r, g, b], axis=0)

    # ---------------------------------------------------------------- render
    def render(self) -> SceneFrame:
        cfg = self.cfg
        h, w = cfg.height, cfg.width
        n = h * w

        ground = self._dz < 0.0
        t = np.where(ground, -cfg.altitude / np.where(ground, self._dz, -1.0), 0.0)
        gx = t * self._dir[0]
        gy = t * self._dir[1]

        gray = np.zeros(n, np.float64)
        gray[ground] = self._ground_gray(gx[ground], gy[ground])

        # objects overwrite the ground
        obj_colors = [(30, 30, 235), (240, 180, 40), (40, 200, 90), (235, 90, 200),
                      (60, 120, 240), (250, 250, 250), (120, 60, 200), (40, 40, 40)]
        rgb = np.zeros((3, n), np.float64)
        rgb[:, ground] = gray[ground][None, :]
        for i, obj in enumerate(self.objects):
            inside = ground & (np.abs(gx - obj.x) <= obj.size / 2.0) & (np.abs(gy - obj.y) <= obj.size / 2.0)
            if inside.any():
                col = np.array(obj_colors[i % len(obj_colors)], np.float64)
                rgb[:, inside] = col[:, None]

        sky = ~ground
        if sky.any():
            rgb[:, sky] = self._sky_rgb()[:, sky]

        image = np.clip(rgb, 0, 255).astype(np.uint8).reshape(3, h, w).transpose(1, 2, 0)
        gray_u8 = np.clip(gray, 0, 255).astype(np.uint8).reshape(h, w)

        boxes = self._object_boxes()
        return SceneFrame(
            rgb=image, gray=gray_u8, objects=self.objects, boxes=boxes,
            pose=self.pose, intrinsics=self.intrinsics,
            horizon_line=self.camera.horizon_line(),
        )

    def _object_boxes(self) -> np.ndarray:
        boxes = []
        for obj in self.objects:
            s = obj.size / 2.0
            corners = [(obj.x - s, obj.y - s), (obj.x + s, obj.y - s),
                       (obj.x + s, obj.y + s), (obj.x - s, obj.y + s)]
            px = [self.camera.ground_to_pixel(cx, cy) for cx, cy in corners]
            if any(p is None for p in px):
                continue
            xs = [p[0] for p in px]
            ys = [p[1] for p in px]
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
            # keep only objects fully inside the frame
            if x1 < 0 or y1 < 0 or x2 >= self.cfg.width or y2 >= self.cfg.height:
                continue
            boxes.append([x1, y1, x2, y2])
        return np.asarray(boxes, np.float32).reshape(-1, 4)

    def __len__(self) -> int:
        return 1
