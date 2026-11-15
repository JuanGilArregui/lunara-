"""Mapas de calor estáticos del polo sur: % de tiempo con Sol y con la Tierra a la vista.

Para cada punto de una cuadrícula (de 80°S al polo) calcula su horizonte con el mapa LOLA y, con SPICE,
cuántas veces el Sol (centro) y la Tierra (borde del disco) quedan por encima de ese horizonte a lo largo
de un año. Guarda dos imágenes (colores fríos -> cálidos sobre el relieve sombreado) en maps/,
que la web muestra en la vista «Surface map». Se ejecuta una vez; la web no necesita servidor.

Uso:  python tools/lola_map.py            (necesita data/lola/LDEM_80S_40M.IMG y kernels/)
Opcional: --grid-km 2  --start 2026-11-10T12:00  --days 365  --step-h 6
"""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lola_horizon import PolarDEM, destination, ROOT, DEFAULT_DEM  # noqa: E402

AZ_STEP = 5  # grados por sector del horizonte
EARTH_ANGULAR_RADIUS = 0.95  # grados (disco de la Tierra visto desde la Luna)


def horizon_grid(dem, lats, lons, mast=2.5):
    """Horizonte (72 azimuts) de cada punto: pasos finos cerca y largos lejos (40 m .. 150 km)."""
    R = dem.radius_m
    dist = np.geomspace(40, 150_000, 160); c = dist / R
    az = np.radians(np.arange(0, 360, AZ_STEP))[:, None]
    out = np.full((len(lats), az.shape[0]), np.nan, dtype=np.float32)
    h0 = dem.height(lats, lons)
    t0 = time.time()
    for i, (lat, lon) in enumerate(zip(lats, lons)):
        if math.isnan(h0[i]): continue
        plat, plon = destination(lat, lon, az, c[None, :])
        h = dem.height(plat, plon)
        ang = np.degrees(np.arctan2((R + h) * np.cos(c) - (R + h0[i] + mast), (R + h) * np.sin(c)))
        out[i] = np.nanmax(np.where(np.isnan(ang), -90, ang), axis=1)
        if i % 5000 == 0 and i: print(f"  horizontes {i:,}/{len(lats):,} ({time.time()-t0:.0f} s)", flush=True)
    return out


def body_directions(start, days, step_h):
    """Direcciones unitarias del Sol y la Tierra vistas desde la Luna (IAU_MOON), con SPICE."""
    import spiceypy as sp
    for k in ('naif0012.tls', 'pck00011.tpc', 'de442s.bsp'):
        sp.furnsh(str(ROOT / 'kernels' / k))
    et0 = sp.str2et(start); n = int(days * 24 / step_h) + 1
    sun, earth = np.empty((n, 3)), np.empty((n, 3))
    for i in range(n):
        et = et0 + i * step_h * 3600
        s, _ = sp.spkpos('SUN', et, 'IAU_MOON', 'NONE', 'MOON'); e, _ = sp.spkpos('EARTH', et, 'IAU_MOON', 'NONE', 'MOON')
        sun[i] = s / np.linalg.norm(s); earth[i] = e / np.linalg.norm(e)
    return sun, earth


def visible_fraction(lats, lons, horizons, dirs, margin=0.0, chunk=64):
    """Fracción de instantes en que la dirección queda por encima del horizonte local de cada punto."""
    p, l = np.radians(lats), np.radians(lons)
    up = np.stack([np.cos(p) * np.cos(l), np.cos(p) * np.sin(l), np.sin(p)], 1)
    east = np.stack([-np.sin(l), np.cos(l), np.zeros_like(l)], 1)
    north = np.stack([-np.sin(p) * np.cos(l), -np.sin(p) * np.sin(l), np.cos(p)], 1)
    nb = horizons.shape[1]; hz = np.nan_to_num(horizons, nan=90.0)
    count = np.zeros(len(lats))
    for k in range(0, len(dirs), chunk):
        d = dirs[k:k + chunk].T                                       # (3, T)
        el = np.degrees(np.arcsin(np.clip(up @ d, -1, 1)))            # (P, T)
        az = np.degrees(np.arctan2(east @ d, north @ d)) % 360
        f = az / AZ_STEP; i0 = np.floor(f).astype(int) % nb; i1 = (i0 + 1) % nb; w = f - np.floor(f)
        h = np.take_along_axis(hz, i0, 1) * (1 - w) + np.take_along_axis(hz, i1, 1) * w
        count += (el + margin > h).sum(1)
    return count / len(dirs)


def median3(a, valid):
    """Mediana 3x3 dentro de la zona válida: quita puntos sueltos (un cráter diminuto en la muestra)."""
    p = np.pad(np.where(valid, a, np.nan), 1, mode='edge')
    stack = np.stack([p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)])
    with np.errstate(all='ignore'):
        import warnings; warnings.simplefilter('ignore', RuntimeWarning)
        return np.where(valid, np.nanmedian(stack, 0), np.nan)


def colorize(frac, shade, valid):
    """Colores fríos (0) -> cálidos (1) sobre el relieve sombreado. Transparente fuera del mapa."""
    stops = np.array([[10, 20, 60], [40, 70, 160], [60, 160, 190], [240, 200, 90], [255, 120, 40]], float)
    pos = np.linspace(0, 1, len(stops)); f = np.clip(frac, 0, 1)
    rgb = np.stack([np.interp(f, pos, stops[:, j]) for j in range(3)], -1)
    rgb *= (0.45 + 0.55 * shade)[..., None]
    alpha = np.where(valid, 255, 0)
    return np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--grid-km', type=float, default=2.0)
    ap.add_argument('--start', default='2026-11-10T12:00:00')
    ap.add_argument('--days', type=float, default=365)
    ap.add_argument('--step-h', type=float, default=6)
    ap.add_argument('--out', type=Path, default=ROOT / 'maps')
    args = ap.parse_args()
    from PIL import Image

    dem = PolarDEM(DEFAULT_DEM); R = dem.radius_m
    half = 300_000  # m: 80°S queda a ~303 km del polo
    n = int(2 * half / (args.grid_km * 1000))
    xs = np.linspace(-half, half, n)
    X, Y = np.meshgrid(xs, xs[::-1])                     # fila 0 = arriba (longitud 0° arriba)
    r = np.hypot(X, Y)
    lat = np.degrees(2 * np.arctan(r / (2 * R)) - np.pi / 2)
    lon = np.degrees(np.arctan2(X, Y))
    valid = r <= half * 0.995  # whole circle inside the square (80°S itself is ~303 km from the pole)
    print(f"Cuadrícula {n}x{n} ({args.grid_km} km): {valid.sum():,} puntos")

    t = time.time(); hz = horizon_grid(dem, lat[valid], lon[valid]); print(f"Horizontes: {time.time()-t:.0f} s")
    t = time.time(); sun, earth = body_directions(args.start, args.days, args.step_h); print(f"SPICE: {len(sun)} instantes, {time.time()-t:.0f} s")
    sun_f = np.full(lat.shape, np.nan); earth_f = np.full(lat.shape, np.nan)
    sun_f[valid] = visible_fraction(lat[valid], lon[valid], hz, sun)
    earth_f[valid] = visible_fraction(lat[valid], lon[valid], hz, earth, margin=EARTH_ANGULAR_RADIUS)
    # Rellenar solo puntos oscuros sueltos (un cráter diminuto en la muestra); las crestas brillantes se conservan
    sun_f, earth_f = np.fmax(sun_f, median3(sun_f, valid)), np.fmax(earth_f, median3(earth_f, valid))
    # Comprobación: valor del mapa en los sitios del catálogo (horizonte fino calculado aparte)
    for name, la, lo in (('Shackleton region', -89.5, 0), ('Shackleton floor', -89.67, 129.78), ('Site A', -89.2, 23.1), ('Site B', -85.0, 23.1)):
        rr = 2 * R * np.tan(np.pi / 4 + np.radians(la) / 2); x, y = rr * np.sin(np.radians(lo)), rr * np.cos(np.radians(lo))
        col, row = np.argmin(abs(xs - x)), np.argmin(abs(xs[::-1] - y))
        print(f"  {name:<18} Sol {sun_f[row, col]*100:5.1f} %   Tierra {earth_f[row, col]*100:5.1f} %")

    # Relieve sombreado (luz desde arriba a la izquierda) a la misma resolución
    hgt = np.full(lat.shape, np.nan); hgt[valid] = dem.height(lat[valid], lon[valid])
    gy, gx = np.gradient(np.nan_to_num(hgt, nan=np.nanmean(hgt)), args.grid_km * 1000)
    slope = np.arctan(np.hypot(gx, gy) * 3); aspect = np.arctan2(-gx, gy)
    shade = np.clip(np.cos(np.radians(45)) * np.cos(slope) + np.sin(np.radians(45)) * np.sin(slope) * np.cos(np.radians(315) - aspect), 0, 1)

    args.out.mkdir(exist_ok=True)
    size = 900
    scales = {'sun': 0.6, 'earth': 1.0}  # valor que se pinta con el color más cálido (la leyenda lo indica)
    for name, frac in (('sun', sun_f), ('earth', earth_f)):
        img = Image.fromarray(colorize(np.nan_to_num(frac) / scales[name], shade, valid), 'RGBA').resize((size, size), Image.BICUBIC)
        img.save(args.out / f'map_{name}.png', optimize=True)
    meta = {'scale_max': scales, 'start_utc': args.start, 'days': args.days, 'step_h': args.step_h, 'grid_km': args.grid_km,
            'extent_m': half, 'latitude_limit': -80, 'projection': 'south polar stereographic, 0°E at the top',
            'source': 'LOLA LDEM_80S_40M horizons + SPICE (de442s) Sun/Earth directions'}
    (args.out / 'maps.json').write_text(json.dumps(meta, indent=1))
    for name, f in (('Sol', sun_f), ('Tierra', earth_f)):
        print(f"{name}: media {np.nanmean(f)*100:.1f} %, máx {np.nanmax(f)*100:.1f} %, puntos a 0 % {np.nansum(f == 0):,}")
    print('->', args.out)


if __name__ == '__main__':
    main()
