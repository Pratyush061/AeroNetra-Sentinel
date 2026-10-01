# AeroNetra-Sentinel — A Friendly Guide

**A companion to `README.md`. If the README felt like a wall of technical words, start here. This guide explains what the project is, why it exists, how to run it, how to test it, and what you can do with it — in plain language.**

---

## 1. What is this, in one minute?

AeroNetra-Sentinel answers a simple but surprisingly hard question:

> **"I can see a car in this photo. But *where on Earth* is it?"**

From **a single photograph** taken by a drone, plus the things a drone already knows about itself, this program works out the **latitude and longitude of every object it can see** — no second camera, no laser rangefinder, no special calibration target on the ground.

---

## 2. Why this is hard, and how it is solved

A camera flattens a three-dimensional world onto a flat picture. Going backwards — from a flat spot in the picture to a real spot on the ground — is normally impossible, because a picture has no depth.

But a drone knows three helpful things about itself:

1. **Where it is** — from its GPS.
2. **How high it is** — from its altimeter.
3. **Which way it is pointing** — from its compass.

The one missing piece is **tilt**: is the camera looking straight down, or off toward the horizon? And here is the neat part — **the tilt can be read straight off the photograph.** The line where the ground meets the sky (the horizon) tilts and shifts exactly in step with the camera's tilt. Find the horizon, and you know the tilt.

Once you know *where*, *how high*, *which way*, and *how tilted*, the ground is completely pinned down. Every spot in the picture maps to exactly one spot on the ground.

> **A helpful way to picture it:** imagine holding a torch in a dark, flat field, with the beam angled down in front of you. If someone tells you exactly how high you are holding it, which way you are facing, and at what angle you are pointing it, they can work out exactly where the pool of light lands. The drone does the same thing with its camera.

---

## 3. The big idea, step by step

1. **Look at the picture.** Find the objects (cars, people, whatever) and draw a box around each one.
2. **Find the horizon.** The sky is smooth and pale; the ground is textured and busy. Where one turns into the other is the horizon. Fit a straight line to it.
3. **Read the tilt.** From that line, work out the camera's downward angle and its sideways lean. No instruments needed — the picture itself tells us.
4. **Build the ground rule.** Combine the tilt, the height and the lens settings into one rule that turns *"this spot in the picture"* into *"this spot on the ground, in metres, to the east and to the north of the drone."*
5. **Convert to latitude and longitude.** Take those east/north metres and add them to the drone's own GPS position. Now every object has real coordinates.
6. **Draw the result.** Boxes labelled with coordinates, a file of points, and a heat map showing where things are crowded.

---

## 4. Why this is interesting

Normally, working out where something is on the ground needs either two cameras (to measure depth by comparing views), a laser rangefinder, or a carefully surveyed marker on the ground.

Sentinel needs **none of those**. It uses one photograph and information the drone already carries. That makes it cheap, light, and useful for small drones that cannot lift heavy equipment — for finding people in search and rescue, mapping traffic, or watching a pipeline.

---

## 5. What is inside

Each part has one job. You do not need to read the code to use it, but here is the map.

| Plain name | Where it lives | What it does |
|---|---|---|
| The map reader | `src/sentinel/geo.py` | Converts between "metres east and north" and latitude/longitude |
| The camera model | `src/sentinel/camera.py` | Knows the lens, the drone's pose, and the rule that links picture to ground |
| The horizon finder | `src/sentinel/horizon.py` | Finds the horizon line and reads the tilt from it |
| The scene maker | `src/sentinel/scene.py` | Draws a pretend aerial view by casting a ray through every pixel — so you can try everything without downloading anything |
| The spotter | `src/sentinel/detect.py` | Finds objects in the picture |
| The locator | `src/sentinel/geolocate.py` | Turns each detection into latitude/longitude, and writes a map file |
| The heat map | `src/sentinel/heatmap.py` | Shows where objects are clustered |
| The conductor | `src/sentinel/pipeline.py` | Runs all of the above in the right order |
| The command line | `src/sentinel/cli.py` | The `sentinel` command you type |

---

## 6. What you need before you start

- A computer running **Windows, macOS or Linux**.
- **Python 3.10 or newer**. Check by typing `python --version` in a terminal.
- About **150 MB of free space** and a few minutes.
- **No graphics card, no internet connection, and no dataset downloads are needed.** The project draws its own pretend scene.

---

## 7. Install it — step by step

Open a terminal and type these lines one at a time.

**Step 1 — get the code**

```bash
git clone https://github.com/Pratyush061/AeroNetra-Sentinel.git
cd AeroNetra-Sentinel
```

**Step 2 — make a private workspace (recommended)**

```bash
python -m venv .venv
```

Switch it on:

- macOS / Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

You will see `(.venv)` at the start of your prompt.

**Step 3 — install the project**

```bash
pip install -e .
```

**Step 4 — check it worked**

```bash
python -c "import sentinel; print(sentinel.__version__)"
```

You should see `0.1.0`.

---

## 8. Run it — and what you will see

```bash
python -m sentinel.cli demo --out outputs
```

(You can also type `sentinel demo`, or `python scripts/run_demo.py`.)

It runs in about a second and prints something like this:

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

Then open the `outputs` folder. You will find:

- **`sentinel_annotated.png`** — the picture with a magenta line drawn along the detected horizon, green boxes around objects, and each box labelled with its latitude and longitude.
- **`detections.geojson`** — a standard map file. You can drag it onto most mapping websites and see the points appear on a real map.
- **`heatmap.png`** — a glow map showing where objects are concentrated.
- **`metrics.json`** — the summary numbers, saved as a file.

### How to read the numbers

| Number | Plain meaning |
|---|---|
| `detections` | How many boxes were drawn |
| `geolocated` | How many of those got real coordinates |
| `ground_truth` | How many objects were really placed in the pretend scene |
| `matched_within_25m` | How many of the real objects were found *and* placed within 25 metres |
| `mean_error_m` | The average distance between our answer and the true answer, in metres |
| `median_error_m` | The typical (middle) error — usually the fairer number |
| `max_error_m` | The worst case |
| `depression_est_deg` | The downward angle we read from the horizon, versus the truth |
| `roll_est_deg` | The sideways lean we read from the horizon, versus the truth |

> A typical error of **about 4 metres** is the headline. That is from a single photograph, with no depth sensor. These numbers come from the built-in pretend scene, so treat them as a demonstration of the *machinery*, not a world record. The scene is fixed with a "seed", so the result repeats every time.

---

## 9. Test it

```bash
pip install -e ".[dev]"
pytest -q
```

You should see `47 passed` (plus a few extra for the roll checks). Each dot is an automatic check confirming a piece of the geometry is correct.

Check the code style too, if you like:

```bash
ruff check .
```

---

## 10. Change how it behaves

Everything adjustable lives in **`configs/default.yaml`**:

- `scene.altitude` — how high the drone is flying, in metres.
- `scene.heading` — which way it is facing, in compass degrees.
- `scene.depression` — how far down it is looking.
- `scene.roll` — how much it is leaning sideways.
- `scene.hfov` — how wide the lens sees.
- `scene.num_objects` — how many objects to place.
- `attitude_source` — `estimated` (read the tilt from the picture) or `true` (use the exact answer, for comparison).
- `reference` — which part of the box to place on the map: `center` or `bottom`.

Then run with your file:

```bash
python -m sentinel.cli run --config configs/default.yaml --out outputs
```

And see which real datasets it can talk to:

```bash
sentinel list-datasets
```

---

## 11. Things to try

- Set `attitude_source: true` and watch the error drop — that shows how much the self-calibration costs.
- Change `scene.altitude` from 120 to 250 and watch the error grow: from higher up, objects are smaller and harder to pin down.
- Set `scene.roll` to 15 and confirm the program still reads the lean from the tilted horizon.
- Set `scene.depression` to 60 (nearly straight down). There is no horizon in view, so the program notices, says so, and falls back safely instead of inventing an answer.

---

## 12. When something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `python: command not found` | Python is not installed | Install Python 3.10+ from python.org, then reopen the terminal |
| `No module named sentinel` | The install step did not finish | Make sure your `(.venv)` is active, then run `pip install -e .` again |
| `attitude_fell_back: true` | The horizon was not visible in the picture | Perfectly normal when looking nearly straight down — the program used the drone's own tilt instead |
| The error numbers look large | The objects were very small in the picture | Fly lower, use a sharper lens, or use a higher-resolution camera |

---

## 13. Word list

- **Latitude / longitude** — the pair of numbers that names any spot on Earth.
- **Horizon** — the line where the ground meets the sky.
- **Tilt** — how far the camera is angled down (depression) and leaning sideways (roll).
- **Homography** — a fancy word for the rule that turns a spot in the picture into a spot on the ground.
- **Ground plane** — the flat surface we assume the objects sit on.
- **Geolocation** — working out real-world coordinates from an image.
- **GeoJSON** — a standard file format for map points.
- **ENU** — "East, North, Up": metres measured from a chosen starting point. Easy to do maths with, then converted to latitude/longitude.
- **Seed** — a fixed starting number, so the pretend scene is the same every time.

---

*Made by Pratyush Jain. MIT licence — see `LICENSE`. For the technical description, read `README.md`; for the reasoning behind the design, read `docs/innovation.md`.*
