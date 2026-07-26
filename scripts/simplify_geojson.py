#!/usr/bin/env python3
"""Stream-simplify a large GeoJSON LineString FeatureCollection for web display.

Reads geojson/bus_routes.geojson (never loading the whole file into memory —
it's parsed one feature at a time) and writes a lighter data/bus_routes.geojson:
duplicate consecutive points are dropped, geometry is simplified with the
Ramer-Douglas-Peucker algorithm, coordinates are rounded to 6 decimal places
(~11cm, far below web-map display resolution), and only the properties useful
for map popups are kept.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "geojson" / "bus_routes.geojson"
OUTPUT_PATH = REPO_ROOT / "data" / "bus_routes.geojson"

SIMPLIFY_EPSILON_DEG = 0.00008  # ~9m at this latitude
COORD_DECIMALS = 6

KEPT_PROPERTIES = [
    "route",
    "route_name",
    "route_variant_name",
    "route_variant_number",
    "directionid",
    "operator_name",
]


def iter_features(path):
    """Yield each Feature dict from a large FeatureCollection without loading it all."""
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8") as f:
        buf = ""
        # Advance until just past the opening '[' of the "features" array.
        while '"features"' not in buf:
            chunk = f.read(1 << 20)
            if not chunk:
                raise ValueError('no "features" key found')
            buf += chunk
        idx = buf.index('"features"')
        idx = buf.index("[", idx) + 1
        buf = buf[idx:]

        while True:
            buf = buf.lstrip()
            while buf.startswith(","):
                buf = buf[1:].lstrip()
            if buf.startswith("]"):
                return
            if not buf:
                chunk = f.read(1 << 20)
                if not chunk:
                    return
                buf += chunk
                continue
            try:
                obj, end = decoder.raw_decode(buf)
            except json.JSONDecodeError:
                chunk = f.read(1 << 20)
                if not chunk:
                    raise
                buf += chunk
                continue
            yield obj
            buf = buf[end:]


def dedup_consecutive(points):
    out = []
    for p in points:
        if not out or p != out[-1]:
            out.append(p)
    return out


def rdp_simplify(points, epsilon):
    """Iterative Ramer-Douglas-Peucker line simplification."""
    n = len(points)
    if n < 3:
        return points

    keep = bytearray(n)
    keep[0] = keep[-1] = 1
    stack = [(0, n - 1)]

    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue

        x1, y1 = points[start]
        x2, y2 = points[end]
        dx, dy = x2 - x1, y2 - y1
        norm = (dx * dx + dy * dy) ** 0.5

        max_dist = -1.0
        max_idx = -1
        for i in range(start + 1, end):
            x0, y0 = points[i]
            if norm == 0:
                dist = ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5
            else:
                dist = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / norm
            if dist > max_dist:
                max_dist = dist
                max_idx = i

        if max_dist > epsilon:
            keep[max_idx] = 1
            stack.append((start, max_idx))
            stack.append((max_idx, end))

    return [p for i, p in enumerate(points) if keep[i]]


def round_coord(pair):
    return [round(pair[0], COORD_DECIMALS), round(pair[1], COORD_DECIMALS)]


def simplify_feature(feature):
    geom = feature.get("geometry") or {}
    if geom.get("type") != "LineString":
        return None

    points = [tuple(c) for c in geom["coordinates"]]
    points = dedup_consecutive(points)
    if len(points) < 2:
        return None
    points = rdp_simplify(points, SIMPLIFY_EPSILON_DEG)

    props = feature.get("properties") or {}
    kept_props = {k: props.get(k) for k in KEPT_PROPERTIES if props.get(k) is not None}

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [round_coord(p) for p in points],
        },
        "properties": kept_props,
    }


def main():
    if not INPUT_PATH.exists():
        print(f"[fatal] {INPUT_PATH} does not exist")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total_in_points = 0
    total_out_points = 0
    written = 0
    skipped = 0

    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        out.write('{"type":"FeatureCollection","features":[')
        first = True
        for i, feature in enumerate(iter_features(INPUT_PATH), start=1):
            in_points = len((feature.get("geometry") or {}).get("coordinates") or [])
            simplified = simplify_feature(feature)
            if simplified is None:
                skipped += 1
                continue

            total_in_points += in_points
            total_out_points += len(simplified["geometry"]["coordinates"])

            if not first:
                out.write(",")
            first = False
            json.dump(simplified, out, separators=(",", ":"))
            written += 1

            if i % 2000 == 0:
                print(f"[progress] processed {i} features ({written} written)")

        out.write("]}")

    print(f"Done. Wrote {written} features ({skipped} skipped) to {OUTPUT_PATH}")
    if total_in_points:
        reduction = 100 * (1 - total_out_points / total_in_points)
        print(f"Vertex count: {total_in_points} -> {total_out_points} ({reduction:.1f}% reduction)")


if __name__ == "__main__":
    main()
