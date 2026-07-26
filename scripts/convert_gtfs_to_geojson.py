#!/usr/bin/env python3
"""Convert a GTFS static feed (gtfs/) into GeoJSON files (data/) for Leaflet."""

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
GTFS_DIR = REPO_ROOT / "gtfs"
DATA_DIR = REPO_ROOT / "data"

DEFAULT_ROUTE_COLOR = "3388FF"
DEFAULT_ROUTE_TEXT_COLOR = "000000"


def read_csv_dicts(path):
    if not path.exists():
        print(f"[warn] {path.name} not found - skipping")
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_stops(gtfs_dir):
    rows = read_csv_dicts(gtfs_dir / "stops.txt")
    if not rows:
        print("[fatal] stops.txt is missing or empty - cannot build a map without stops")
        sys.exit(1)
    return rows


def build_stops_geojson(stop_rows):
    features = []
    for row in stop_rows:
        stop_id = row.get("stop_id", "")
        try:
            lat = float(row["stop_lat"].strip())
            lon = float(row["stop_lon"].strip())
        except (KeyError, ValueError, AttributeError):
            print(f"[warn] skipping stop {stop_id!r} - missing/invalid stop_lat or stop_lon")
            continue

        properties = {
            "stop_id": stop_id,
            "stop_name": row.get("stop_name", "") or "",
            "location_type": row.get("location_type", "") or "",
        }
        if row.get("stop_code"):
            properties["stop_code"] = row["stop_code"]

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def load_routes(gtfs_dir):
    rows = read_csv_dicts(gtfs_dir / "routes.txt")
    return {row["route_id"]: row for row in rows if row.get("route_id")}


def load_trips(gtfs_dir):
    rows = read_csv_dicts(gtfs_dir / "trips.txt")
    mapping = {}
    for row in rows:
        shape_id = row.get("shape_id")
        route_id = row.get("route_id")
        if shape_id and route_id:
            mapping.setdefault(shape_id, route_id)
    return mapping


def load_shapes(gtfs_dir):
    rows = read_csv_dicts(gtfs_dir / "shapes.txt")
    if not rows:
        print("[warn] shapes.txt missing/empty - no route lines will be generated")
        return {}

    grouped = {}
    for row in rows:
        shape_id = row.get("shape_id")
        try:
            seq = int(row["shape_pt_sequence"])
            lat = float(row["shape_pt_lat"])
            lon = float(row["shape_pt_lon"])
        except (KeyError, ValueError, TypeError):
            print(f"[warn] skipping malformed shape point in shape {shape_id!r}")
            continue
        if not shape_id:
            continue
        grouped.setdefault(shape_id, []).append((seq, lat, lon))

    shapes = {}
    for shape_id, points in grouped.items():
        points.sort(key=lambda p: p[0])
        shapes[shape_id] = [(lat, lon) for _, lat, lon in points]
    return shapes


def build_shapes_geojson(shapes, shape_to_route, routes):
    features = []
    for shape_id, points in shapes.items():
        if len(points) < 2:
            print(f"[warn] skipping shape {shape_id!r} - fewer than 2 points")
            continue

        route_id = shape_to_route.get(shape_id)
        route = routes.get(route_id, {})

        route_color = (route.get("route_color") or "").strip().lstrip("#") or DEFAULT_ROUTE_COLOR
        route_text_color = (
            (route.get("route_text_color") or "").strip().lstrip("#") or DEFAULT_ROUTE_TEXT_COLOR
        )

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lat, lon in points],
                },
                "properties": {
                    "shape_id": shape_id,
                    "route_id": route_id or "",
                    "route_short_name": route.get("route_short_name") or shape_id,
                    "route_long_name": route.get("route_long_name") or "",
                    "route_color": route_color,
                    "route_text_color": route_text_color,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def write_geojson(obj, path):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def main():
    if not GTFS_DIR.exists():
        print(f"[fatal] {GTFS_DIR} does not exist - create it and add GTFS .txt files")
        sys.exit(1)

    stops_fc = build_stops_geojson(load_stops(GTFS_DIR))

    routes = load_routes(GTFS_DIR)
    trips_map = load_trips(GTFS_DIR)
    shapes = load_shapes(GTFS_DIR)
    shapes_fc = build_shapes_geojson(shapes, trips_map, routes)

    write_geojson(stops_fc, DATA_DIR / "stops.geojson")
    write_geojson(shapes_fc, DATA_DIR / "shapes.geojson")

    print(f"Wrote {len(stops_fc['features'])} stops to data/stops.geojson")
    print(f"Wrote {len(shapes_fc['features'])} shapes to data/shapes.geojson")


if __name__ == "__main__":
    main()
