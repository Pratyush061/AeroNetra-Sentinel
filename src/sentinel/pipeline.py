"""End-to-end single-frame geo-registration pipeline."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from . import viz
from .camera import GroundCamera, Intrinsics, Pose
from .config import SentinelConfig
from .detect import detect_objects
from .geolocate import geolocate, match_errors, to_geojson
from .heatmap import density_grid, heatmap_rgb
from .horizon import estimate_attitude
from .scene import GeoScene, SceneFrame


class SentinelPipeline:
    """Single-frame monocular geo-registration."""

    def __init__(self, cfg: SentinelConfig):
        self.cfg = cfg
        self.intrinsics = Intrinsics.from_hfov(cfg.scene.width, cfg.scene.height, cfg.scene.hfov)
        self.true_pose = Pose(
            cfg.scene.lat0, cfg.scene.lon0, cfg.scene.altitude,
            cfg.scene.heading, cfg.scene.depression, cfg.scene.roll,
        )

    def _resolve_pose(self, frame: SceneFrame):
        """Return (pose_used, attitude_report)."""
        cfg = self.cfg
        if cfg.attitude_source == "true":
            return self.true_pose, {
                "source": "true", "depression_est": cfg.scene.depression,
                "roll_est": cfg.scene.roll, "inlier_ratio": 1.0, "fell_back": False,
            }

        estimate = estimate_attitude(frame.gray, self.intrinsics.K, cfg.horizon, seed=cfg.scene.seed)
        if estimate is None:
            return self.true_pose, {
                "source": "true(fallback)", "depression_est": cfg.scene.depression,
                "roll_est": cfg.scene.roll, "inlier_ratio": 0.0, "fell_back": True,
            }
        depression, roll, ratio = estimate
        # Yaw is not observable from a horizontal plane's vanishing line, so the
        # compass supplies heading; the horizon supplies tilt.
        pose = replace(self.true_pose, depression=depression, roll=roll)
        return pose, {
            "source": "estimated", "depression_est": depression,
            "roll_est": roll, "inlier_ratio": ratio, "fell_back": False,
        }

    def run(self, frame: SceneFrame | None = None, out_dir=None) -> dict:
        cfg = self.cfg
        out_dir = Path(out_dir or cfg.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if frame is None:
            frame = GeoScene(cfg.scene).render()

        pose, attitude = self._resolve_pose(frame)
        camera = GroundCamera(self.intrinsics, pose)

        detections = detect_objects(frame.rgb, cfg.detect)
        objects = geolocate(detections, camera, pose, reference=cfg.reference)

        truth = [(o.lat, o.lon) for o in frame.objects]
        errors, matched = match_errors(objects, truth)
        finite = [e for e in errors if np.isfinite(e)]

        grid = density_grid(objects, cfg.heatmap_extent, cfg.heatmap_resolution)
        if cfg.save_heatmap:
            import cv2

            cv2.imwrite(str(out_dir / "heatmap.png"), heatmap_rgb(grid))

        (out_dir / "detections.geojson").write_text(json.dumps(to_geojson(objects), indent=2))

        hud = [
            f"attitude: {attitude['source']}",
            f"depression est/true: {attitude['depression_est']:.1f}/{cfg.scene.depression:.1f} deg",
            f"roll est/true: {attitude['roll_est']:.1f}/{cfg.scene.roll:.1f} deg",
            f"geolocated: {len(objects)}",
        ]
        annotated = viz.annotate(frame.rgb, detections, objects, camera.horizon_line(), hud)
        import cv2

        cv2.imwrite(str(out_dir / "sentinel_annotated.png"),
                    cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))

        summary = {
            "detections": len(detections),
            "geolocated": len(objects),
            "ground_truth": len(truth),
            "matched_within_25m": matched,
            "mean_error_m": round(float(np.mean(finite)), 3) if finite else None,
            "median_error_m": round(float(np.median(finite)), 3) if finite else None,
            "max_error_m": round(float(np.max(finite)), 3) if finite else None,
            "attitude_source": attitude["source"],
            "attitude_fell_back": attitude["fell_back"],
            "depression_est_deg": round(attitude["depression_est"], 3),
            "depression_true_deg": cfg.scene.depression,
            "depression_error_deg": round(attitude["depression_est"] - cfg.scene.depression, 3),
            "roll_est_deg": round(attitude["roll_est"], 3),
            "roll_true_deg": cfg.scene.roll,
            "horizon_inlier_ratio": round(attitude["inlier_ratio"], 3),
            "heatmap_max_count": float(grid.max()),
            "outputs": {
                "annotated": str(out_dir / "sentinel_annotated.png"),
                "geojson": str(out_dir / "detections.geojson"),
                "heatmap": str(out_dir / "heatmap.png") if cfg.save_heatmap else None,
            },
        }
        (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2))
        return summary


def run_demo(cfg: SentinelConfig | None = None, out_dir=None) -> dict:
    """Render the synthetic georeferenced scene and geo-register it."""
    cfg = cfg or SentinelConfig()
    return SentinelPipeline(cfg).run(out_dir=out_dir)
