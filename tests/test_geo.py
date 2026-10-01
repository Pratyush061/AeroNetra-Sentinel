

from sentinel.geo import bearing, enu_to_latlon, haversine, latlon_to_enu


def test_enu_roundtrip():
    lat0, lon0 = 18.5204, 73.8567  # Pune
    for lat, lon in [(18.5214, 73.8577), (18.5100, 73.8400), (18.5300, 73.8700)]:
        e, n = latlon_to_enu(lat, lon, lat0, lon0)
        lat2, lon2 = enu_to_latlon(e, n, lat0, lon0)
        assert abs(lat2 - lat) < 1e-9
        assert abs(lon2 - lon) < 1e-9


def test_enu_axes_point_the_right_way():
    lat0, lon0 = 0.0, 0.0
    east, north = latlon_to_enu(0.0, 0.001, lat0, lon0)
    assert east > 0 and abs(north) < 1e-6
    east, north = latlon_to_enu(0.001, 0.0, lat0, lon0)
    assert north > 0 and abs(east) < 1e-6


def test_haversine_matches_known_distance():
    # ~111.32 km per degree of latitude at the equator
    d = haversine(0.0, 0.0, 1.0, 0.0)
    assert abs(d - 111319.5) < 50.0


def test_bearing_cardinal():
    assert abs(bearing(0.0, 0.0, 1.0, 0.0) - 0.0) < 1e-6      # north
    assert abs(bearing(0.0, 0.0, 0.0, 1.0) - 90.0) < 1e-6     # east
    assert abs(bearing(0.0, 0.0, -1.0, 0.0) - 180.0) < 1e-6   # south


def test_enu_scale_is_metric():
    # 1e-4 degrees of latitude is ~11.13 m
    _, north = latlon_to_enu(1e-4, 0.0, 0.0, 0.0)
    assert abs(north - 11.132) < 0.05
