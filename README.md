# Transit Mapping

A static website that visualizes bus route data on a [Leaflet](https://leafletjs.com/)
map, using a [CartoDB Positron](https://carto.com/basemaps) basemap.

**Coordinate reference systems**: the bus routes layer is WGS84 (EPSG:4326)
lat/lng. The states/territories layer is kept in its native **GDA2020**
(EPSG:7844) — see below for why. The Leaflet map itself always renders on
Web Mercator (EPSG:3857): every public raster basemap tile provider (CartoDB,
OSM, ...) only serves tiles in that projection, so it's fixed regardless of
what CRS the vector data is in. Leaflet projects incoming lat/lng values with
spherical Web Mercator math without a datum-aware transform, so GDA2020 and
WGS84 coordinates render side by side with no visible seam — the two datums
differ by only ~1.5-2m in real-world position.

## Requirements

- Python 3
- Any modern web browser
- `scripts/simplify_geojson.py` and `scripts/convert_gtfs_to_geojson.py` use
  only the standard library. `scripts/convert_states_shapefile.py` (state
  boundaries) additionally needs `geopandas`, `shapely`, and `pyproj`.

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

## State/territory boundaries (background layer)

`data/states.geojson` — Australian state/territory outlines rendered as a
light gray context layer beneath the bus routes — is generated from the ABS
`STE_2021_AUST_SHP_GDA2020` shapefile in `data/STE_2021_AUST_SHP_GDA2020/`:

```
python3 scripts/convert_states_shapefile.py
```

This keeps the shapefile's native **GDA2020 (EPSG:7844)** coordinates rather
than reprojecting to WGS84 — the output's `crs` member declares
`urn:ogc:def:crs:EPSG::7844` accordingly. It also simplifies the coastlines
(`SIMPLIFY_TOLERANCE_DEG` in the script, default ~200m) — the raw shapefile
has ~1.8M vertices across 10 states/territories at full cartographic detail
(down to tiny offshore islands), far more than a background layer needs. On
this dataset that's 29 MB → 3.6 MB.

This layer is optional — if `data/states.geojson` isn't present, the site
still loads and just shows the bus routes without it (a console warning is
logged, nothing breaks). Popups are disabled on this layer; it's
display/context only and isn't listed in the legend.

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
geojson/                      raw input GeoJSON (yours to replace)
gtfs/                         raw GTFS input files, alternate pipeline (sample fixture included)
data/STE_2021_AUST_SHP_GDA2020/  raw ABS states/territories shapefile
data/                          generated/simplified GeoJSON actually served to the browser
scripts/                       simplify_geojson.py, convert_gtfs_to_geojson.py, convert_states_shapefile.py
assets/                        frontend CSS/JS
index.html                     entry point
```

## Attribution

Map tiles: CartoDB Positron, © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, © [CARTO](https://carto.com/attributions).
