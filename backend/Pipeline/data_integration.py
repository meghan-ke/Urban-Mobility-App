"""
Integrating the trip data with the zone lookup data.
"""

import pandas as pd
from pathlib import Path
import sys


# Add backend_dir to sys.path so we can import config.py
backend_dir = Path(__file__).resolve().parents[1]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from config import PROCESSED_DATA_PATH
from .data_loader import load_trip_data, load_zone_lookup
from .data_cleaning import clean_data
from .feature_engineering import engineer_features


def intergrate_data():
    
    """
    this function merges the two data sets together using the PULocationID.
    """

    print("Integrating datasets ...")

    trip_data = load_trip_data()

    print(f"STEP 2: Type of trip_data AFTER load: {type(trip_data)}")
    
    print("STEP 3: About to call clean_data...")
    
    trip_data, exclusion_log = clean_data(trip_data)

    # engineer new features
    trip_data = engineer_features(trip_data)
    print(f"   Result: {trip_data.shape[0]:,} rows & {trip_data.shape[1]} columns")

    zone_lookup = load_zone_lookup()

    print(f"STEP 5: Zone lookup type: {type(zone_lookup)}")

    merged_data = trip_data.merge(zone_lookup,
            left_on = "PULocationID",
            right_on = "LocationID",
            how = "left"
        )
    print(f"Integration complete: {merged_data.shape[0]} rows, {merged_data.shape[1]} columns")

     # Save cleaned and merged data to processed folder
    output_path = project_root / PROCESSED_DATA_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_data.to_csv(output_path, index=False)
    print(f"Saved cleaned data to: {output_path}")


    return merged_data




if __name__ == "__main__":
    print("Integrating data...")
    merge = intergrate_data()
    print(merge.head())
    print(merge.columns)