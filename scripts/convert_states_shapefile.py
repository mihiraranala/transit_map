#!/usr/bin/env python3
"""Convert the ABS Australian states/territories shapefile to a web-sized GeoJSON.

Reads data/STE_2021_AUST_SHP_GDA2020/STE_2021_AUST_GDA2020.shp (GDA2020 /
EPSG:7844), reprojects it to WGS84 (EPSG:4326) to match the rest of the site,
simplifies the very high-resolution coastlines (the raw file has ~1.8M
vertices across 10 states/territories — full cartographic detail down to
tiny islands, far more than a background context layer needs), and writes
data/states.geojson.

Requires geopandas + shapely + pyproj (already installed in this environment).
"""

from pathlib import Path

import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parent.parent
SHAPEFILE_PATH = REPO_ROOT / "data" / "STE_2021_AUST_SHP_GDA2020" / "STE_2021_AUST_GDA2020.shp"
OUTPUT_PATH = REPO_ROOT / "data" / "states.geojson"

SIMPLIFY_TOLERANCE_DEG = 0.002  # ~200m, fine for a background/context layer

KEEP_COLUMNS = {
    "STE_CODE21": "state_code",
    "STE_NAME21": "state_name",
    "AREASQKM21": "area_sqkm",
}


def main():
    gdf = gpd.read_file(SHAPEFILE_PATH)
    print(f"Read {len(gdf)} features, CRS={gdf.crs}")

    gdf = gdf.to_crs(epsg=4326)

    gdf["geometry"] = gdf["geometry"].simplify(SIMPLIFY_TOLERANCE_DEG, preserve_topology=True)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]

    gdf = gdf.rename(columns=KEEP_COLUMNS)[list(KEEP_COLUMNS.values()) + ["geometry"]]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_PATH, driver="GeoJSON")

    print(f"Wrote {len(gdf)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
