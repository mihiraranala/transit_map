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

const NSW_COLOR = '#0b2545';
const OTHER_STATE_COLOR = '#ffffff';
const ROUTE_COLOR = '#2b6cb0';

function stateStyle(feature) {
  if (feature.properties.state_name === 'New South Wales') {
    return {
      color: NSW_COLOR,
      weight: 2.5,
      fillColor: NSW_COLOR,
      fillOpacity: 0.08,
      opacity: 1,
    };
  }
  return {
    color: OTHER_STATE_COLOR,
    weight: 1,
    fillColor: OTHER_STATE_COLOR,
    fillOpacity: 0.4,
    opacity: 0.4,
  };
}

function renderStates(geojson) {
  return L.geoJSON(geojson, {
    style: stateStyle,
  }).addTo(map);
}

function addLegend() {
  const legend = L.control({ position: 'topleft' });
  legend.onAdd = () => {
    const div = L.DomUtil.create('div', 'legend');
    L.DomEvent.disableClickPropagation(div);
    div.innerHTML = `
      <div class="legend-title">Legend</div>
      <div class="legend-item">
        <span class="legend-swatch legend-swatch-line" style="background:${ROUTE_COLOR}"></span>
        Bus routes
      </div>
    `;
    return div;
  };
  legend.addTo(map);
}

function renderRoutes(geojson) {
  return L.geoJSON(geojson, {
    style: () => ({
      color: ROUTE_COLOR,
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
  let statesResp, routesResp;
  try {
    [statesResp, routesResp] = await Promise.all([
      fetch('data/states.geojson'),
      fetch('data/bus_routes.geojson'),
    ]);
  } catch (err) {
    showError('Failed to fetch data/*.geojson. Are you serving this over HTTP (not file://)?');
    return;
  }

  if (!routesResp.ok) {
    showError('Failed to load data/bus_routes.geojson — run scripts/simplify_geojson.py first.');
    return;
  }

  // States is a background context layer — render it before routes so routes
  // sit on top, but don't fail the whole page if it's missing.
  if (statesResp.ok) {
    const statesData = await statesResp.json();
    renderStates(statesData);
  } else {
    console.warn('data/states.geojson not found — run scripts/convert_states_shapefile.py to add it.');
  }

  const routesData = await routesResp.json();
  const routesLayer = renderRoutes(routesData);
  fitMapToLayers(routesLayer);
}

addLegend();
loadData();
