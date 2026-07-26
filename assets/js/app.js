const map = L.map('map', { preferCanvas: true });

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
    '&copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 19,
}).addTo(map);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]));
}

function renderRoutes(geojson) {
  return L.geoJSON(geojson, {
    style: () => ({
      color: '#2b6cb0',
      weight: 2,
      opacity: 0.65,
    }),
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      const title = p.route_name || p.route_variant_name || p.route || 'Unknown route';
      let html = `<strong>${escapeHtml(title)}</strong>`;
      if (p.route) html += `<br>Route ${escapeHtml(p.route)}`;
      if (p.directionid) html += ` &middot; ${escapeHtml(p.directionid)}`;
      if (p.operator_name) html += `<br>${escapeHtml(p.operator_name)}`;
      layer.bindPopup(html);
    },
  }).addTo(map);
}

function fitMapToLayers(...layers) {
  let bounds = null;
  for (const layer of layers) {
    const b = layer.getBounds();
    if (!b.isValid()) continue;
    bounds = bounds ? bounds.extend(b) : b;
  }
  if (bounds && bounds.isValid()) {
    map.fitBounds(bounds, { padding: [20, 20] });
  } else {
    map.setView([0, 0], 2);
  }
}

function showError(message) {
  const div = document.createElement('div');
  div.className = 'map-error';
  div.textContent = message;
  document.body.appendChild(div);
}

async function loadData() {
  let resp;
  try {
    resp = await fetch('data/bus_routes.geojson');
  } catch (err) {
    showError('Failed to fetch data/bus_routes.geojson. Are you serving this over HTTP (not file://)?');
    return;
  }

  if (!resp.ok) {
    showError('Failed to load data/bus_routes.geojson — run scripts/simplify_geojson.py first.');
    return;
  }

  const geojson = await resp.json();
  const routesLayer = renderRoutes(geojson);
  fitMapToLayers(routesLayer);
}

loadData();
