// Page behaviour (the layout itself is plain HTML in index.html):
//  - focused views (overlay): open with any [data-open-view] button, close with ←, Esc or a click outside
//  - ⤢ full screen for each 3D view (Esc or the button again to close)
//  - ▶ play dock on the local sky view, kept in sync with the main #play button; Space = play / pause
//  - coordinates shown in the Scenario card
// Runs while the page is parsed (before the main app scripts).
(() => {
  const $id = id => document.getElementById(id);

  // ---- Focused views (telemetry, comparison, explorer, limitations) ----
  const overlay = $id('novaViewOverlay');
  const views = [...document.querySelectorAll('.nova-view')];
  let opener = null;
  function openView(key, button) {
    const view = views.find(v => v.dataset.view === key);
    if (!view) return;
    views.forEach(v => v.classList.toggle('is-active', v === view));
    overlay.classList.toggle('is-wide', key === 'comparison'); // the comparison uses the full screen
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('nova-view-open');
    opener = button || null;
    view.querySelector('.nova-close')?.focus({ preventScroll: true });
  }
  function closeView() {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('nova-view-open');
    views.forEach(v => v.classList.remove('is-active'));
    opener?.focus?.({ preventScroll: true });
    opener = null;
  }
  document
    .querySelectorAll('[data-open-view]')
    .forEach(b => b.addEventListener('click', () => openView(b.dataset.openView, b)));
  document.querySelectorAll('.nova-close').forEach(b => b.addEventListener('click', closeView));
  overlay?.addEventListener('click', event => {
    if (event.target === overlay) closeView();
  });

  // ---- ⤢ Full screen for the 3D views (the scenes follow their container size) ----
  const expandedPanel = () => document.querySelector('#visuals > .panel.is-expanded');
  function setExpanded(panel, on) {
    panel.classList.toggle('is-expanded', on);
    document.body.classList.toggle('nova-view-expanded', on);
    const button = panel.querySelector('.nova-expand');
    button.textContent = on ? '✕' : '⤢';
    button.setAttribute('aria-label', on ? 'Close full screen' : 'Expand to full screen');
  }
  document.querySelectorAll('#visuals > .panel').forEach(panel => {
    panel.querySelector('.nova-expand')?.addEventListener('click', () => {
      const open = expandedPanel();
      if (open && open !== panel) setExpanded(open, false);
      setExpanded(panel, !panel.classList.contains('is-expanded'));
    });
  });

  // ---- Keyboard: Esc closes, Space plays / pauses ----
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const open = expandedPanel();
      if (open) setExpanded(open, false);
      else if (overlay?.classList.contains('is-open')) closeView();
      return;
    }
    if (event.code !== 'Space' || event.repeat) return;
    if (event.target.closest?.('input, select, textarea, button, [contenteditable]')) return;
    event.preventDefault();
    const compareOpen = document.querySelector('.nova-view.is-active[data-view="comparison"]');
    $id(compareOpen ? 'comparePlay' : 'play')?.click();
  });

  // ---- ▶ Play dock on the local sky view, mirroring the main #play button ----
  const mainPlay = $id('play'),
    readout = $id('timeReadout'),
    dock = document.querySelector('.sky-play');
  if (mainPlay && dock) {
    const dockBtn = dock.querySelector('.sky-play__btn'),
      dockTime = dock.querySelector('.sky-play__time');
    const sync = () => {
      const playing = /pause/i.test(mainPlay.textContent);
      dockBtn.textContent = playing ? 'Ⅱ' : '▶';
      dockBtn.setAttribute('aria-label', playing ? 'Pause' : 'Play');
      dock.classList.toggle('is-playing', playing);
      mainPlay.classList.toggle('is-playing', playing);
      if (readout) dockTime.textContent = readout.textContent.replace(/:\d\d UTC$/, ' UTC');
    };
    dockBtn.addEventListener('click', () => mainPlay.click());
    const watch = { childList: true, characterData: true, subtree: true };
    new MutationObserver(sync).observe(mainPlay, watch);
    if (readout) new MutationObserver(sync).observe(readout, watch);
    sync();
  }

  // ---- Coordinates under the Scenario controls ----
  const coords = document.querySelector('.nova-coordinate-tag');
  const showCoords = () => {
    const lat = Number($id('lat')?.value || 0),
      lon = Number($id('lon')?.value || 0);
    coords.textContent = `${Math.abs(lat).toFixed(2)}°${lat < 0 ? 'S' : 'N'} · ${Math.abs(lon).toFixed(2)}°${lon < 0 ? 'W' : 'E'}`;
  };
  if (coords) {
    showCoords();
    ['lat', 'lon'].forEach(id => $id(id)?.addEventListener('input', showCoords));
    $id('preset')?.addEventListener('change', () => requestAnimationFrame(showCoords));
  }
})();
