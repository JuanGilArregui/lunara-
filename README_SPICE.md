# LUNARA — local NASA/JPL SPICE server

The browser does not run SPICE itself. A small local Python server (`lunara_spice_server.py`) loads the NAIF
kernels, computes the Sun and Earth position vectors and returns them as JSON in the format LUNARA already
reads. The same server also serves the web app, so everything runs from `http://127.0.0.1:8765/`.

## 1. Requirements

- Python 3.9 or newer (on Windows, with the `py` launcher).
- [SpiceyPy](https://github.com/AndrewAnnex/SpiceyPy) (`requirements_spice.txt`).
- The kernels are already included in `kernels/`. Internet access is only needed to install SpiceyPy
  or to download a kernel that is missing.

## 2. Starting the server

**Windows:** double-click `start_lunara_spice.bat`. It installs SpiceyPy if needed, starts the server
with `--download-missing` and opens the browser.

**Any OS:**

```bash
python -m pip install -r requirements_spice.txt
python lunara_spice_server.py --kernel-dir kernels --html index.html
```

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Address to listen on (local machine only) |
| `--port` | `8765` | HTTP port |
| `--kernel-dir` | `kernels` | Folder with the SPK, LSK and PCK kernels |
| `--html` | `index.html` | Page served at `/` |
| `--download-missing` | off | Download missing kernels from the official NAIF server |

Keep the terminal open while using the app. If the kernels cannot be loaded, the page still opens in demo mode.

## 3. Using it in the app

Use the **Demo / Real · SPICE** switch in the top bar. When it is on, the app asks the server for the
positions over the selected window (start date, duration and step) and uses them for every calculation.
The status of the server and of the loaded kernels is shown under **Data source**.

## 4. API

| Endpoint | Description |
|---|---|
| `GET /api/status` | Whether SPICE is ready and which kernels are loaded |
| `GET /api/ephemeris?start_utc=YYYY-MM-DDTHH:MM&duration_hours=24&step_minutes=15` | Sun and Earth vectors for the window |

Limits enforced by the server:

- `duration_hours`: 1 to 8784 (one year).
- `step_minutes`: 10, 15, 30, 60, 180 or 360.
- At most 20,000 samples per request; long windows need a larger step.

Invalid parameters return `400`. Requests are processed one at a time, because SPICE is not thread-safe.

## 5. Kernels

The server looks for these exact file names in `kernels/`:

- `de442s.bsp`: JPL DE442s planetary ephemeris (preferred). `de440s.bsp` is accepted as a compatible fallback.
- `naif0012.tls`: leap seconds, for UTC ↔ ET/TDB conversion.
- `pck00011.tpc`: physical constants and the standard `IAU_MOON` orientation.

With `--download-missing`, missing files are downloaded from the NAIF generic kernels:

- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de442s.bsp
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp (fallback)
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls
- https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc

## 6. What is computed

For each time step in the window the server:

- Converts the UTC time to SPICE ET/TDB using the LSK.
- Computes the geometric position of `SUN` relative to `MOON`.
- Computes the geometric position of `EARTH` relative to `MOON`.
- Returns both vectors in kilometres in the `IAU_MOON` frame.

Aberration correction is `NONE`, so the vectors are geometric positions consistent with the app's geometric
model. Local geometry, elevation, azimuth, visibility, charts and metrics are still computed in LUNARA's
JavaScript. The server never extrapolates outside the SPK coverage: SPICE returns an error instead.

## 7. Accuracy

These are **real SPICE ephemerides**, but LUNARA's local coordinates use `IAU_MOON`, and `pck00011.tpc`
only provides the standard low-precision lunar orientation. NAIF recommends the binary lunar PCKs and the
`MOON_ME` / `MOON_PA` frames for high-precision lunar orientation.

This makes LUNARA suitable for development, visualization and prototyping of geometric analyses, but it is
not a certified tool for landing site selection or mission decisions. Earth visibility is geometric and does
not by itself mean an RF link is available.

## 8. Troubleshooting

- **"SPICE service not detected"**: open the app at `http://127.0.0.1:8765/`, not by double-clicking `index.html`.
- **Missing kernels**: check that the files are in `kernels/` with the exact names above, or run with `--download-missing`.
- **SpiceyPy cannot be installed**: run `python -m pip install -r requirements_spice.txt` (`py -m pip …` on Windows) in a terminal.
- **"Date is outside SPICE file coverage"**: choose a date covered by DE442s/DE440s.
- **Frame error in the terminal**: check that `pck00011.tpc` downloaded completely and is in `kernels/`.
- **Port already in use**: start the server with another `--port`.

## Official sources

- NAIF Generic Kernels: https://naif.jpl.nasa.gov/naif/data_generic.html
- NAIF PCK/FK summary for the Moon and Earth (orientation accuracy and frame selection): https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/23_lunar-earth_pck-fk.pdf
