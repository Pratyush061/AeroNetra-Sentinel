"""WGS84 / local tangent-plane geodesy helpers.

All local work is done in a metric East-North-Up (ENU) frame anchored at the
UAV's ground position. The equirectangular approximation used here is accurate
to well under a metre over the few-kilometre span a single UAV frame covers.
"""

from __future__ import annotations

import math

R_EARTH = 6378137.0  # WGS84 semi-major axis, metres


def latlon_to_enu(lat: float, lon: float, lat0: float, lon0: float):
    """Geographic -> local ENU metres relative to ``(lat0, lon0)``."""
    dlat = math.radians(lat - lat0)
    dlon = math.radians(lon - lon0)
    east = dlon * math.cos(math.radians(lat0)) * R_EARTH
    north = dlat * R_EARTH
    return east, north


def enu_to_latlon(east: float, north: float, lat0: float, lon0: float):
    """Local ENU metres -> geographic coordinates."""
    lat = lat0 + math.degrees(north / R_EARTH)
    lon = lon0 + math.degrees(east / (R_EARTH * math.cos(math.radians(lat0))))
    return lat, lon


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2.0 * R_EARTH * math.asin(min(1.0, math.sqrt(a)))


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2, in compass degrees [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlam)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
