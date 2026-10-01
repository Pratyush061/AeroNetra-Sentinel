<div align="center">

# AeroNetra-Sentinel

### Single-frame monocular geo-registration for UAVs

**Turn one image into real coordinates — object latitude/longitude, with no stereo, no LiDAR, no calibration target.**

[![CI](https://github.com/Pratyush061/AeroNetra-Sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/Pratyush061/AeroNetra-Sentinel/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)

</div>

> **New here?** Read the **[Friendly Guide](GUIDE.md)** — a plain-language walkthrough of what this does, how to run it, how to test it, and what to do with it.

---

## Why this exists

A UAV that detects a vehicle knows *where it is in the frame* — not *where it is
on Earth*. Recovering coordinates usually means stereo, LiDAR or a surveyed
calibration target. Sentinel does it from **a single frame**, using the three
things a UAV already has: its GPS position, its altitude, and its compass.

The missing piece is **tilt** — and that is recoverable from the image itself.
The ground plane's vanishing line (the horizon) gives the plane normal, hence
depression and roll. With tilt, altitude and heading, the ground plane is fully
determined and every detected pixel maps to a real coordinate.

> This is breakthrough **#2** of four. It runs with **zero downloads**.

---

## The pipeline

```
  one image ──► self-calibrating horizon ──► depression, roll ┐
                                                              ├─► ground-plane homography
  compass (heading) + altitude (barometer/GPS) ───────────────┘         │
                                                                        ▼
  detections ──► reference pixel ──► ground (E, N) ──► lat/lon ──► GeoJSON + heatmap
```

| Stage | Module | What it does |
|---|---|---|
| Geodesy | `sentinel.geo` | WGS84 ⇄ local ENU, haversine, bearing |
| Camera | `sentinel.camera` | pinhole model, pose, ground homography, horizon line |
| Horizon | `sentinel.horizon` | texture-onset + RANSAC line fit → attitude |
| Scene | `sentinel.scene` | ray-cast georeferenced scene with ground-truth coordinates |
| Detect | `sentinel.detect` | single-frame local-contrast detector |
| Geolocate | `sentinel.geolocate` | pixel → lat/lon, GeoJSON, error scoring |
| Heatmap | `sentinel.heatmap` | geospatial density grid |
| Orchestrate | `sentinel.pipeline` | threads it together, prints the accuracy |

---

## Quickstart

```bash
git clone https://github.com/Pratyush061/AeroNetra-Sentinel.git
cd AeroNetra-Sentinel

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

python -m sentinel.cli demo --out outputs
# or:  sentinel demo
# or:  python scripts/run_demo.py
```

Output:

```
AeroNetra-Sentinel — demo complete
  detections: 11
  geolocated: 11
  ground_truth: 8
  matched_within_25m: 8
  mean_error_m: 5.568
  median_error_m: 4.083
  max_error_m: 17.479
  attitude_source: estimated
  depression_est_deg: 25.5      (true 25.0)
  roll_est_deg: -0.0            (true 0.0)
  horizon_inlier_ratio: 1.0
```

You get an annotated frame (boxes labelled with lat/lon, the detected horizon
drawn), a **GeoJSON** of geolocated points, a **heatmap** PNG and `metrics.json`.

> Numbers are from the built-in synthetic georeferenced scene and illustrate the
> *pipeline*, not a benchmark claim. The scene is seeded, so they reproduce.

```bash
sentinel list-datasets        # geo-tagged aerial & satellite datasets
sentinel run --config configs/default.yaml
```

---

## How it works

**1. Ground-plane homography.** With intrinsics `K`, camera-to-world rotation
`R_wc` and altitude `h`, the pixel→ground map is a homography built from
`M = R_wc K⁻¹`. Altitude supplies the metric scale.

**2. Self-calibrating tilt.** For a plane with camera normal `n`, the vanishing
line is `l = K⁻ᵀ n`. We estimate `l` from the image (sky/ground texture
boundary + RANSAC), then invert it: `n = Kᵀ l`, giving depression and roll.

**3. Geolocation.** Each detection's reference pixel → ground offset `(E, N)` in
metres → latitude/longitude via a local ENU conversion anchored at the UAV.

**Yaw is not observable from the horizon** — a horizontal plane's vanishing line
constrains tilt, not rotation about it — so heading comes from the compass. This
is stated plainly rather than hidden.

---

## Datasets — geo-tagged first

Geo-registration needs geographic metadata, so Sentinel favours **geo-tagged**
data: **AU-AIR** (UAV imagery + GPS/IMU flight logs), **SeaDronesSee**,
**UAVDT**, **UAVid**, **MARS**, **DOTA**, and satellite sets **SpaceNet** and
**xBD**. VisDrone is included but flagged *not geo-tagged* — it has no per-frame
GPS. See [`docs/datasets.md`](docs/datasets.md).

---

## Configuration

Everything is a typed dataclass (`sentinel.config`) overridable from YAML. Key
knobs: altitude, heading, depression, roll, field of view, `attitude_source`
(`estimated` vs `true`), the detection reference point, and heatmap extent.

---

## Project layout

```
AeroNetra-Sentinel/
├── src/sentinel/       # geo, camera, horizon, scene, detect, geolocate, heatmap, pipeline, cli
├── configs/            # YAML configuration
├── scripts/            # run_demo.py
├── tests/              # pytest suite (runs without downloads)
├── docs/               # architecture, datasets, innovation notes
└── .github/workflows/  # CI: lint + tests + demo smoke run
```

---

## Testing & quality

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

CI runs lint, the full suite and a demo smoke run on Python 3.10–3.12.

---

## Roadmap — four breakthroughs

1. [AeroNetra-Orion](https://github.com/Pratyush061/AeroNetra-Orion) — event-driven predictive perception
2. **AeroNetra-Sentinel** — single-frame monocular geo-registration ← *you are here*
3. Swarm consensus perception (occlusion-resilient multi-UAV counting)
4. Adverse-condition robust fusion (thermal + RGB + dehazing with test-time adaptation)

---

## License

MIT © 2026 Pratyush Jain. See [LICENSE](LICENSE).
