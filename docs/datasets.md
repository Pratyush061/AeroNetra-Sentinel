# Datasets

Geo-registration needs data that carries **geographic** information — the camera
pose and the labels in coordinates. This project therefore favours **geo-tagged**
aerial and satellite datasets rather than detection-only benchmarks.

```bash
sentinel list-datasets
```

| Key | Geo-tagged | Modality | Why it matters here |
|---|---|---|---|
| `auair` | yes | low-altitude UAV RGB + flight logs | GPS/IMU logs give the pose; imagery gives the scene |
| `seadronessee` | yes | maritime UAV RGB | geo-referenced small-object search |
| `uavdt` | yes | aerial RGB video | sequences carry flight metadata |
| `uavid` | yes | aerial semantic video | recording metadata |
| `mars` | yes | multi-agent UAV tracking | world-coordinate trajectories |
| `dota` | yes | aerial oriented boxes | large geo-referenced tiles |
| `spacenet` | yes | satellite imagery | labels in coordinates |
| `xbd` | yes | satellite before/after | geo-located damage labels |
| `visdrone` | no | aerial detection/tracking | widely used — but no per-frame GPS |

## Expected layout

```
data/<key>/
```

`require(key)` raises a `FileNotFoundError` carrying the download URL if the
folder is missing.

## Flight logs

The one thing a geo-registration pipeline needs that a detection dataset lacks is
the camera pose. `parse_flight_log()` reads a small JSON log:

```json
{ "lat": 18.5204, "lon": 73.8567, "altitude": 120.0,
  "heading": 0.0, "depression": 25.0, "roll": 0.0 }
```

`lat`, `lon`, `altitude` are required; the attitude fields default sensibly.
