# LUNARA · Lunar Mission Intelligence

Mission planner for the lunar south pole. It compares landing sites by how much sunlight they get
(solar power) and how long they can see Earth (direct-to-Earth communications), using real NASA/JPL SPICE
ephemerides and LOLA terrain from the Lunar Reconnaissance Orbiter.

- **Main view:** 3D sky around the site with LOLA terrain, 2D horizon, window metrics and timeline.
- **Link to Earth:** DSN station visibility (Goldstone, Madrid, Canberra) and link budget.
- **Comparison studio:** up to 4 scenarios side by side, with charts over time and CSV export.
- **Surface map:** sunlight and Earth-visibility heat maps of the whole south pole (2 km grid).

## Requirements

- Python 3.9 or newer (on Windows, with the `py` launcher).
- A modern browser with WebGL (Chrome, Edge or Firefox).
- Internet access only the first time, to install SpiceyPy. Three.js and the SPICE kernels are already in the repo.

## Running it

### Windows

Double-click `start_lunara_spice.bat`. It installs SpiceyPy if needed, starts the server and opens
`http://127.0.0.1:8765/`. Keep the terminal open while you use the app.

### Any OS

```bash
python -m pip install -r requirements_spice.txt
python lunara_spice_server.py --kernel-dir kernels --html index.html
```

Then open `http://127.0.0.1:8765/`. Useful options: `--port 9000` and `--download-missing`
(downloads any missing kernels from NAIF).

> Do not open `index.html` by double-clicking it (`file://`): the browser blocks loading the modules and CSV files.
> Without the SPICE server the app still works in **demo mode** with synthetic data.

## Testing it

There are no automated tests yet. This is the manual check to run before every push.

### 1. Server and API

With the server running, in another terminal:

```bash
curl http://127.0.0.1:8765/api/status
# → "ready": true and the three kernels loaded

curl "http://127.0.0.1:8765/api/ephemeris?start_utc=2026-11-15T00:00&duration_hours=24&step_minutes=60"
# → JSON with 25 samples of Sun and Earth vectors in IAU_MOON (km)

curl "http://127.0.0.1:8765/api/ephemeris?start_utc=2026-11-15T00:00&duration_hours=24&step_minutes=7"
# → 400 error: invalid step_minutes (checks input validation)
```

Quick check that the Python scripts compile:

```bash
python -m py_compile lunara_spice_server.py tools/lola_horizon.py tools/lola_map.py inspect_lola_dem.py
```

### 2. User interface

Open the browser console (F12) and check that no red errors appear on load.

| What to test | Expected result |
|---|---|
| Load the page | Intro screen, then the observatory with the 3D sky scene |
| **Demo / Real · SPICE** switch | Switches to real data and the badge no longer says `DEMO MODE` |
| Change site in **Scenario** (e.g. Shackleton crater floor) | The LOLA horizon changes and the metrics are recalculated |
| Window buttons **1 d … 1 yr** | The window is recalculated; 1 year takes a few seconds |
| **▶ Play** or the space bar | Sun and Earth move across the sky and the timeline advances |
| **＋ Add to comparison**, then open **Compare scenarios** | The scenario fills a free slot; ★ marks the best value in each row |
| **Surface map**, ☀ / ◉ buttons | South pole heat maps appear with the catalog sites marked |
| **Export mission report ↗** and **Export CSV** | The report and the comparison CSV are downloaded |
| Stop the server and reload | The app keeps working in demo mode and warns that SPICE is unavailable |

## Regenerating data (optional)

Horizons (`horizons/*.csv`) and maps (`maps/*.png`) are already precomputed. You only need to regenerate
them when adding new sites or changing the method:

```bash
python -m pip install numpy spiceypy
python tools/lola_horizon.py --download   # first time only: downloads the LOLA map (~460 MB) to data/lola/
python tools/lola_horizon.py              # writes horizons/<site>.csv
python tools/lola_map.py                  # writes maps/ (about 2 min)
```

To inspect high-resolution LOLA GeoTIFFs: `python -m pip install rasterio numpy matplotlib`, then
`python inspect_lola_dem.py <file.tif>`.

`data/lola/` is not committed. The steps to add a new site are in [js/README.md](js/README.md).

## Project structure

```
index.html                 main page
css/                       styles (load order matters)
js/                        front-end, explained file by file in js/README.md
vendor/three/              bundled Three.js r160 so the app works offline
models/                    3D models (.glb) and textures
horizons/                  precomputed LOLA horizons per site
maps/                      sunlight and Earth-visibility heat maps
kernels/                   SPICE kernels (DE442s, LSK, PCK)
lunara_spice_server.py     local server: serves the app and the ephemeris API
tools/                     Python scripts that generate horizons and maps
inspect_lola_dem.py        inspection of high-resolution LOLA GeoTIFFs
```

More details: [js/README.md](js/README.md) (front-end) and [README_SPICE.md](README_SPICE.md) (SPICE server and accuracy).

## Limitations

This is a visualization and prototyping tool, not certified for mission decisions. Lunar orientation uses
`IAU_MOON` (low precision) and Earth visibility is geometric; it does not guarantee an RF link.
The 3D models are illustrative. The app's **Model integrity** view explains this in detail.

## License

The code is released under the [MIT License](LICENSE). Third-party content keeps its own terms:
Three.js (`vendor/three/`) is MIT-licensed, and the SPICE kernels and LOLA data come from NASA/JPL.

## Team and contributions

All the code was pushed to this repository from a single account. This is who actually built each part:

| Person | GitHub | Contribution |
|---|---|---|
| **Sey** | [@seyamacuba](https://github.com/seyamacuba) | Initial app prototype (`index.html`). Python SPICE server (`lunara_spice_server.py`), `.bat` launcher, NAIF kernel selection and `README_SPICE.md`. |
| **Victor** | [@imVictorVM](https://github.com/imVictorVM) | 3D models and textures (Moon, antenna, solar panel, Sun, Earth, starry sky). 3D scene lighting, solar panel that tracks the Sun and wiring the panel to the data. |
| **Nicole** | [@Miegu](https://github.com/Miegu) | First high-resolution LOLA data (Site04, 5 m/px) and the `inspect_lola_dem.py` script to inspect it and generate previews. |
| **Juan** | [@JuanGilArregui](https://github.com/JuanGilArregui) | Split of the app into `css/` and `js/` modules. LOLA terrain: per-site horizons (`tools/lola_horizon.py`) and heat maps (`tools/lola_map.py`, Surface map view). Link to Earth (DSN and link budget), date ranges, full-screen comparison studio with charts, SPICE switch, playback (Play), readability and code formatting. |

Built for the NASA Space Apps Challenge 2026.
