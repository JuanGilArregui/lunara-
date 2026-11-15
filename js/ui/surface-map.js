'use strict';
// "Surface map" view: static heat maps of the south pole (share of time with the Sun / the Earth above the
// local terrain over one year). The images are precomputed by tools/lola_map.py into maps/; this file only
// switches the layer, sets the legend and places the catalog sites on the map. The map is not clickable.
// Part of LUNARA's main app. Loaded as a classic deferred script (see js/README.md for the order).

(() => {
  const img = document.getElementById('mapImage');
  if (!img) return;
  const MAP_EXTENT_M = 300000; // half width of the map (tools/lola_map.py), 80°S is ~303 km from the pole
  const MOON_R_M = 1737400;
  let scales = { sun: 0.6, earth: 1 }; // colour used for the warmest value (from maps/maps.json)
  const layers = {
    sun: { src: 'maps/map_sun.png', alt: 'South polar map of the share of time with sunlight' },
    earth: { src: 'maps/map_earth.png', alt: 'South polar map of the share of time with the Earth in view' }
  };

  function showLayer(key) {
    img.src = layers[key].src;
    img.alt = layers[key].alt;
    document.getElementById('mapLegendMax').textContent =
      scales[key] < 1 ? `≥ ${Math.round(scales[key] * 100)} %` : '100 %';
    document
      .querySelectorAll('[data-map-layer]')
      .forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mapLayer === key)));
  }
  document
    .querySelectorAll('[data-map-layer]')
    .forEach(b => b.addEventListener('click', () => showLayer(b.dataset.mapLayer)));

  // Catalog sites with LOLA terrain, placed with the same south polar stereographic projection as the map.
  const markers = document.getElementById('mapMarkers');
  const sites = Object.values(PRESETS).filter(p => p.horizon);
  sites.forEach((p, i) => {
    const r = 2 * MOON_R_M * Math.tan(Math.PI / 4 + (p.lat * Math.PI) / 360);
    const x = r * Math.sin((p.lon * Math.PI) / 180),
      y = r * Math.cos((p.lon * Math.PI) / 180);
    const el = document.createElement('span');
    el.className = 'surface-map__site';
    el.style.left = `${((x + MAP_EXTENT_M) / (2 * MAP_EXTENT_M)) * 100}%`;
    el.style.top = `${((MAP_EXTENT_M - y) / (2 * MAP_EXTENT_M)) * 100}%`;
    el.textContent = String(i + 1); // numbered: several sites are close to the pole; names are listed below
    el.title = p.name;
    markers.appendChild(el);
  });
  document.getElementById('mapSites').innerHTML = sites
    .map((p, i) => `<span><b>${i + 1}</b>${escapeHtml(p.name)}</span>`)
    .join('');

  // Period and colour scale used when the maps were generated.
  fetch('maps/maps.json', { cache: 'no-store' })
    .then(r => (r.ok ? r.json() : null))
    .then(meta => {
      if (!meta) return;
      if (meta.scale_max) scales = meta.scale_max;
      const start = new Date(meta.start_utc + 'Z'),
        end = new Date(start.getTime() + meta.days * 86400000);
      const fmt = d =>
        d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
      document.getElementById('mapNote').textContent =
        `South pole from 80°S · ${fmt(start)} – ${fmt(end)} · LOLA terrain + SPICE positions · ` +
        `${meta.grid_km} km grid: it shows regions; the exact values of a site are in the main view.`;
      showLayer(document.querySelector('[data-map-layer][aria-pressed="true"]')?.dataset.mapLayer || 'sun');
    })
    .catch(() => {});
})();
