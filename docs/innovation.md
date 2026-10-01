# The innovation, stated honestly

Recovering the geographic coordinates of objects from a **single monocular
frame**, with no stereo, no LiDAR and no calibration target, is the goal. Each
ingredient below has prior art; the contribution is the coherent, reproducible
system and its self-calibrating attitude step.

## The idea

A UAV already knows three things: where it is (GPS), how high it is (barometer),
and which way it points (compass). If it can also recover its **tilt** from the
image itself, then the ground plane is fully determined and every detected pixel
maps to a real coordinate.

## Ingredients and prior art (be candid)

| Ingredient | Prior art exists | Sentinel's contribution |
|---|---|---|
| Ground-plane homography from a calibrated camera | Yes (classical photogrammetry) | Wired end-to-end from a single frame to GeoJSON |
| Vanishing line ↔ plane normal (`l = K⁻ᵀ n`) | Yes (standard result) | Used to *self-calibrate* attitude from the horizon |
| Horizon / vanishing-line detection | Yes | A texture-onset + RANSAC estimator that rejects sky-only columns |
| ENU ↔ WGS84 local conversion | Yes | Small, tested, no heavy geodesy dependency |
| Geospatial heatmaps | Yes | Derived directly from geolocated points |

## What is genuinely new here

1. **Self-calibrating tilt.** Attitude (depression, roll) is recovered from the
   horizon line and the intrinsics alone — no IMU, no calibration target — and
   the recovered tilt then drives geolocation.
2. **One frame, real coordinates.** No temporal filtering, no stereo baseline,
   no LiDAR. Altitude supplies scale; the horizon supplies tilt; the compass
   supplies yaw.
3. **A measurable accuracy claim.** On the synthetic georeferenced scene the
   median geolocation error is a few metres, and the demo prints it.

## Falsifiable claims

- `l = K⁻ᵀ n` and its inverse recover attitude exactly:
  `tests/test_camera.py::test_attitude_roundtrip_from_normal`.
- The horizon estimator recovers depression/roll from a rendered image within a
  couple of degrees, and returns `None` when the horizon is out of frame:
  `tests/test_horizon.py`.
- Geolocation matches known ground points to sub-metre precision in closed form:
  `tests/test_geolocate.py::test_geolocate_matches_known_ground_point`.

## What this is not

- Not validated on a real geo-tagged dataset in this repository; the demo is
  synthetic and seeded.
- Assumes a locally flat ground plane — hills break it, and that is stated.
- Yaw is **not** recoverable from the horizon; a compass is required.

Honesty about the boundary is part of the design. Breakthroughs #3 and #4 extend it.
