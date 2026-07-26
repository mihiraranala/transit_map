# Transit Mapping

A static website that visualizes bus route data on a [Leaflet](https://leafletjs.com/)
map, using a [CartoDB Positron](https://carto.com/basemaps) basemap. Coordinates
are WGS84 (EPSG:4326) lat/lng, which is also Leaflet's native coordinate system,
so the data is displayed as-is with no reprojection.

## Requirements

- Python 3 (standard library only — no `pip install` needed)
- Any modern web browser

## Setup — using your own GeoJSON

The site currently loads `data/bus_routes.geojson`, generated from
`geojson/bus_routes.geojson` (a raw NSW bus-routes export — `LineString`
features per route variant, at very high coordinate precision and vertex
density: 433 MB / 17,589 features / ~10.5M points).

1. Drop your raw GeoJSON at `geojson/bus_routes.geojson` (or edit `INPUT_PATH`
   in the script below to point elsewhere).

2. Simplify it for web display:

   ```
   python3 scripts/simplify_geojson.py
   ```

   This streams through the input file (it never loads the whole thing into
   memory, so it's safe to run against very large exports), dedupes repeated
   points, applies Ramer–Douglas–Peucker line simplification
   (`SIMPLIFY_EPSILON_DEG` in the script, default ~9m), rounds coordinates to
   6 decimal places (~11cm — far below web-map display resolution), and keeps
   only the properties used in map popups (`route`, `route_name`,
   `route_variant_name`, `route_variant_number`, `directionid`,
   `operator_name` — edit `KEPT_PROPERTIES` to change this). On the NSW bus
   routes export this cuts 433 MB → 54 MB (a 79.5% vertex reduction) while
   keeping every one of the 17,589 route features.

   Output is written to `data/bus_routes.geojson`, overwriting anything
   already there. Rerun this any time the source GeoJSON changes.

3. Serve the site locally (a real HTTP server is required — the page's
   `fetch()` call for the GeoJSON is blocked by browsers when opened directly
   via `file://`):

   ```
   python3 -m http.server 8000
   ```

4. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Setup — using GTFS instead

If you have a GTFS static feed (stops.txt/routes.txt/trips.txt/shapes.txt)
instead of pre-built GeoJSON, `scripts/convert_gtfs_to_geojson.py` converts it
to `data/stops.geojson` + `data/shapes.geojson` (see the script for details; a
small sample feed is seeded in `gtfs/`). You'd then need to point
`assets/js/app.js` at those files instead of `data/bus_routes.geojson` — the
two pipelines aren't wired together automatically since a feed normally comes
from one source or the other.

## Project layout

```
geojson/    raw input GeoJSON (yours to replace)
gtfs/       raw GTFS input files, alternate pipeline (sample fixture included)
data/       generated/simplified GeoJSON actually served to the browser
scripts/    simplify_geojson.py, convert_gtfs_to_geojson.py
assets/     frontend CSS/JS
index.html  entry point
```

## Attribution

Map tiles: CartoDB Positron, © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, © [CARTO](https://carto.com/attributions).
