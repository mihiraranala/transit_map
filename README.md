# Transit Mapping

A static website that visualizes GTFS (General Transit Feed Specification) stops
and route shapes on a [Leaflet](https://leafletjs.com/) map, using a
[CartoDB Positron](https://carto.com/basemaps) basemap. GTFS coordinates are
already WGS84 (EPSG:4326) lat/lng, which is also Leaflet's native coordinate
system, so the data is displayed as-is with no reprojection.

## Requirements

- Python 3 (standard library only — no `pip install` needed)
- Any modern web browser

## Setup

1. Place your GTFS `.txt` files in the `gtfs/` folder, replacing the sample
   fixture that's there by default. `stops.txt` is required; `routes.txt`,
   `trips.txt`, and `shapes.txt` are optional but needed for route lines and
   route names in popups.

2. Convert GTFS to GeoJSON:

   ```
   python3 scripts/convert_gtfs_to_geojson.py
   ```

   This writes `data/stops.geojson` and `data/shapes.geojson`, overwriting
   anything already there. Rerun this any time the contents of `gtfs/` change.

3. Serve the site locally (a real HTTP server is required — the page's
   `fetch()` calls for the GeoJSON files are blocked by browsers when opened
   directly via `file://`):

   ```
   python3 -m http.server 8000
   ```

4. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project layout

```
gtfs/       raw GTFS input files (yours to replace)
data/       generated GeoJSON (overwritten by the conversion script)
scripts/    convert_gtfs_to_geojson.py
assets/     frontend CSS/JS
index.html  entry point
```

## Attribution

Map tiles: CartoDB Positron, © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, © [CARTO](https://carto.com/attributions).
