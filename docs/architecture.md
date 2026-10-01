# Architecture

## Data flow

```
                 ┌──────────────────────────────┐
   one image ───►│ horizon estimate (RANSAC)     │──► depression, roll
                 └──────────────────────────────┘        │
                                                          ▼
   compass (heading) ──────────────────────────────► UAV attitude
                                                          │
   altitude (barometer/GPS) ──────────────────────► ground-plane homography
                                                          │
   detections ──► reference pixel ──► H ──► ground (east, north) m ──► lat/lon
                                                          │
                                        ┌─────────────────┴─────────────────┐
                                        ▼                                   ▼
                                  GeoJSON points                 geospatial heatmap
```

## Modules

| Module | Responsibility | Key types |
|---|---|---|
| `config` | Typed, YAML-overridable configuration | `SentinelConfig` |
| `geo` | WGS84 / local ENU geodesy | `latlon_to_enu`, `enu_to_latlon`, `haversine` |
| `camera` | Pinhole geometry, pose, ground homography, horizon | `Intrinsics`, `Pose`, `GroundCamera` |
| `horizon` | Self-calibrating horizon estimation | `estimate_horizon`, `estimate_attitude` |
| `scene` | Ray-cast georeferenced scene with ground truth | `GeoScene`, `SceneFrame` |
| `detect` | Single-frame local-contrast detector | `Detection` |
| `geolocate` | Pixel -> ground -> lat/lon, GeoJSON, scoring | `GeoObject` |
| `heatmap` | Geospatial density grid | `density_grid` |
| `pipeline` | Orchestration and metrics | `SentinelPipeline` |
| `viz`, `cli`, `datasets` | Drawing, command line, adapters | |

## The one equation that matters

For a plane with camera-frame normal `n`, the vanishing line is `l = K⁻ᵀ n`, and
the ground-plane homography from a pixel `p` is

```
        ⎡ -h·M₀₀  -h·M₀₁  -h·M₀₂ ⎤
H  =    ⎢ -h·M₁₀  -h·M₁₁  -h·M₁₂ ⎥ ,   M = R_wc · K⁻¹ ,   h = altitude
        ⎣  M₂₀     M₂₁     M₂₂   ⎦
```

so `ground = (Hp)₀:₂ / (Hp)₂`. Altitude supplies the metric scale; the horizon
supplies the tilt; the compass supplies the yaw.

## Design decisions

**Yaw is not observable from the horizon.** A horizontal plane's vanishing line
constrains the plane normal (tilt), not rotation about it. So the horizon gives
depression and roll; heading must come from the compass. This is stated plainly
rather than papered over.

**Graceful degradation.** If the horizon is not in frame (high depression), the
estimator returns `None` and the pipeline falls back to the supplied attitude,
recording `attitude_fell_back: true`.

**Determinism.** The scene is seeded; the demo and its error metric reproduce.
