"""Geolocation of detections from a single frame.

Each detection's reference pixel is mapped through the ground-plane homography
to a metric ground offset from the UAV, then converted to latitude/longitude
using the UAV's own ground position. This is the whole point of the project:
one frame, one altitude, real coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .camera import GroundCamera, Pose
from .detect import Detection
from .geo import enu_to_latlon, haversine


@dataclass
class GeoObject:
    """A geolocated object."""

    lat: float
    lon: float
    east: float
    north: float
    box: tuple[float, float, float, float]
    score: float
    label: str = "object"

    @property
    def range_m(self) -> float:
        """Horizontal distance from the UAV, metres."""
        return math.hypot(self.east, self.north)

    def to_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [self.lon, self.lat]},
            "properties": {
                "label": self.label,
                "score": round(float(self.score), 3),
                "range_m": round(self.range_m, 2),
                "east_m": round(self.east, 2),
                "north_m": round(self.north, 2),
            },
        }


def geolocate(
    detections: list[Detection],
    camera: GroundCamera,
    pose: Pose,
    reference: str = "center",
) -> list[GeoObject]:
    """Geolocate detections that fall below the horizon."""
    objects: list[GeoObject] = []
    for det in detections:
        u, v = det.reference_point(reference)
        ground = camera.pixel_to_ground(u, v)
        if ground is None:
            continue
        lat, lon = enu_to_latlon(ground[0], ground[1], pose.lat, pose.lon)
        objects.append(GeoObject(lat, lon, ground[0], ground[1], det.box, det.score, det.label))
    return objects


def to_geojson(objects: list[GeoObject]) -> dict:
    """A GeoJSON FeatureCollection of geolocated points."""
    return {"type": "FeatureCollection", "features": [o.to_feature() for o in objects]}


def match_errors(
    objects: list[GeoObject],
    truth: list[tuple[float, float]],
    max_match_m: float = 25.0,
):
    """For each ground-truth point, distance to the nearest geolocated object.

    Returns ``(errors_m, matched_count)`` where an object counts as matched when
    it lands within ``max_match_m`` of the truth.
    """
    errors: list[float] = []
    matched = 0
    for tlat, tlon in truth:
        if not objects:
            errors.append(float("nan"))
            continue
        best = min(haversine(tlat, tlon, o.lat, o.lon) for o in objects)
        errors.append(best)
        if best <= max_match_m:
            matched += 1
    return errors, matched
