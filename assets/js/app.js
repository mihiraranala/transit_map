const map = L.map('map');

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

function renderShapes(geojson) {
  return L.geoJSON(geojson, {
    style: (feature) => ({
      color: '#' + (feature.properties.route_color || '3388FF'),
      weight: 3,
      opacity: 0.8,
    }),
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      const title = p.route_short_name || p.route_long_name || p.shape_id;
      let html = `<strong>${escapeHtml(title)}</strong>`;
      if (p.route_long_name) html += `<br>${escapeHtml(p.route_long_name)}`;
      layer.bindPopup(html);
    },
  }).addTo(map);
}

function renderStops(geojson) {
  return L.geoJSON(geojson, {
    pointToLayer: (feature, latlng) =>
      L.circleMarker(latlng, {
        radius: 5,
        fillColor: '#e6550d',
        color: '#fff',
        weight: 1,
        fillOpacity: 0.9,
      }),
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      let html = `<strong>${escapeHtml(p.stop_name || 'Unnamed stop')}</strong>`;
      if (p.stop_code) html += `<br>Code: ${escapeHtml(p.stop_code)}`;
      html += `<br>ID: ${escapeHtml(p.stop_id)}`;
      layer.bindPopup(html);
    },
  }).addTo(map);
}

function fitMapToData(...geojsonLayers) {
  const combined = L.geoJSON(geojsonLayers);
  const bounds = combined.getBounds();
  if (bounds.isValid()) {
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
  let stopsResp, shapesResp;
  try {
    [stopsResp, shapesResp] = await Promise.all([
      fetch('data/stops.geojson'),
      fetch('data/shapes.geojson'),
    ]);
  } catch (err) {
    showError('Failed to fetch data/*.geojson. Are you serving this over HTTP (not file://)?');
    return;
  }

  if (!stopsResp.ok || !shapesResp.ok) {
    showError('Failed to load data/*.geojson — run scripts/convert_gtfs_to_geojson.py first.');
    return;
  }

  const [stopsData, shapesData] = await Promise.all([stopsResp.json(), shapesResp.json()]);

  renderShapes(shapesData);
  renderStops(stopsData);
  fitMapToData(stopsData, shapesData);
}

loadData();
