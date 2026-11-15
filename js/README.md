# LUNARA front-end structure

`index.html` holds the page HTML exactly as it is shown (nothing is moved around on load). Styles live in `css/`
and code in `js/`. Each person can work on their own files without stepping on anyone else's.

## Running it

Double-click `start_lunara_spice.bat` and open `http://127.0.0.1:8765/`.
Do not open `index.html` by double-clicking it (`file://`): the browser does not load the separate files properly.

Three.js is bundled in `vendor/three/` (it is not downloaded from the internet), so the app loads fast and works offline.

## What each file contains

| File | Contents |
|---|---|
| `js/core/state.js` | Constants, shared state (`ephemeris`, `rows`, `currentScenario`…) and helpers (`$`, `clamp`, vectors) |
| `js/core/ephemeris.js` | Sun and Earth positions: demo mode and `positions.json` reader |
| `js/core/geometry.js` | Local geometry, horizon, elevation/azimuth, visibility intervals |
| `js/core/comms.js` | Communications with Earth: DSN station visibility and link budget («Link to Earth» panel) |
| `js/data/terrain.js` | Terrain horizons per site: loads the LOLA CSVs from `horizons/` and user-uploaded CSVs |
| `js/ui/horizon-2d.js` | 2D horizon view (Sun and Earth around the site); used by the main column and the comparison studio |
| `js/ui/render.js` | Renders metrics, window summary, elevation chart and timeline |
| `js/ui/scenes-3d.js` | Three.js scenes: local sky with LOLA relief and «Link to Earth» panel (Moon, Earth, DSN stations); 2D fallback view |
| `js/ui/comparison.js` | Comparison studio (4 slots, add sites from the free slot, 3D/2D, ★ best value) and site finder |
| `js/ui/surface-map.js` | «Surface map» view: shows the heat maps in `maps/` (Sun / Earth) and marks the catalog sites |
| `js/data/files.js` | Loads `positions.json` and horizon CSVs; exports reports |
| `js/app/controls.js` | `calculate()` and the listeners of the main controls |
| `js/data/spice-bridge.js` | Connection to the Python SPICE server |
| `js/boot.js` | Startup: loads Three.js, builds the scenes and runs the first calculation |
| `js/workspace-controller.js` | Page behaviour: opening/closing views, full screen ⤢, Play control and space bar |
| `js/intro.js` | Intro screen |
| `css/01-…` to `css/09-…` | Base styles and earlier redesigns (with dead and overridden rules removed) |
| `css/10-data-panel.css` | Right data column (scenario, summary, 2D view, readings, tools) |
| `css/11-compare.css` | Full-screen comparison studio and «Compare over time» charts |
| `css/12-readability.css` | Minimum readable font size (~12-13 px) in every view; loaded last |

## LOLA terrain: adding a site

The LOLA height map (hundreds of MB) is never loaded by the web app. Each catalog site's horizon is precomputed
(a ~8 KB CSV) and the app only loads that file:

1. Add the site to `tools/sites_south_pole.csv` (name, lat, lon).
2. `python tools/lola_horizon.py --download` (first time only: downloads the map to `data/lola/`, ignored by git).
3. `python tools/lola_horizon.py` → writes `horizons/<name>.csv`.
4. Add the site to `PRESETS` in `js/core/state.js` (with `horizon: 'horizons/<name>.csv'`) and its `<option>` in `index.html`.

## Heat maps («Surface map»)

`maps/map_sun.png` and `maps/map_earth.png` are precomputed images (no server needed):
`python tools/lola_map.py` (about 2 min; needs the LOLA map in `data/lola/` and `kernels/`).
Every point of a 2 km grid gets its LOLA horizon and, with SPICE, the script counts over one year how often
the Sun (centre) and the Earth (edge of the disc) are above it. It shows regions, not exact values.

## Two important rules

**1. The order of the `<script defer>` tags in `index.html` matters.**
The files in `js/core`, `js/ui`, `js/data`, `js/app` and `js/boot.js` are classic scripts (not modules):
whatever one declares at the top level (`let`, `const`, `function`) is visible to the others.

- Using something from another file **inside a function** always works.
- Using it **directly at load time** (outside a function) only works if that other file comes earlier in the list.
- `boot.js` always goes last.
- Do not declare the same name in two different files (it throws an error).
- Do not use `await` outside a function (only valid in modules); if needed, put it in `boot.js`.
- A new file needs its own `<script defer src="…">` in `index.html`, in the right place.

**2. The order of the CSS files matters too.** When two rules clash, the one in the later file wins.
To change something in the design, edit the rule in the earliest file in the list that defines it,
or add the changes to the file for the section you are working on.

## Code formatting

The code is formatted with Prettier (config in `.prettierrc.json`):

```
npx prettier@3.3.3 --write "js/**/*.js" "css/*.css"
```

Run it before committing: it keeps everyone's changes clean and reduces conflicts.
