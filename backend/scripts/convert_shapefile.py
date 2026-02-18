# backend/scripts/convert_shapefile.py
import geopandas as gpd
from pathlib import Path
import sys

# parents[1] = Urban-Mobility-App/backend   config.py lives here
# parents[2] = Urban-Mobility-App           Data/ lives here
backend_dir = Path(__file__).resolve().parents[1]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from config import ZONES_SHP_PATH

shapefile_path = project_root / ZONES_SHP_PATH

print("Looking for shapefile:")
print(f"  {shapefile_path}")
if not shapefile_path.exists():
    print("\nShapefile not found.")
    print("Please check that the Data folder exists and that the shapefile path is correct.")
    print(f"Expected at: {shapefile_path}")
    sys.exit(1)

print("Reading shapefile...")
gdf = gpd.read_file(str(shapefile_path))
gdf = gdf.to_crs(epsg=4326)
geojson_path = shapefile_path.with_suffix('.geojson')
gdf.to_file(str(geojson_path), driver='GeoJSON')
print(f"Saved GeoJSON to: {geojson_path}")