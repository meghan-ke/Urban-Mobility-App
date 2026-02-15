"""
phase 1: Load the raw data set.
"""
import pandas as pd
from backend.config import TRIP_DATA_PATH, ZONE_LOOKUP_PATH

def load_trip_data():
    """
    Load trip parquet data.
    """
    print("load trip data")
    tp = pd.read_csv(TRIP_DATA_PATH)
    print("trip data loaded")
    print(tp.head())
    return tp

def load_zone_lookup():
    """
    Load zone lookup csv.
    """
    print("Loading zone lookup data")
    zl = pd.read_csv(ZONE_LOOKUP_PATH)
    print(zl.head())
    print("zone lookup data loaded")
    return zl


if __name__ == "__main__":
    print("Loading data...")
    load_trip_data()
    load_zone_lookup()
