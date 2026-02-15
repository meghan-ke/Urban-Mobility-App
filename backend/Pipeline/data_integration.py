"""
Integrating the trip data with the zone lookup data.
"""

import pandas as pd
from .data_loader import load_trip_data, load_zone_lookup
from .data_cleaning import clean_data

def intergrate_data():
    
    """
    this function merges the two data sets together using the PULocationID.
    """

    print("Integrating datasets ...")

    trip_data = load_trip_data()

    print(f"STEP 2: Type of trip_data AFTER load: {type(trip_data)}")
    
    print("STEP 3: About to call clean_data...")
    
    trip_data, exclusion_log = clean_data(trip_data)



    zone_lookup = load_zone_lookup()

    print(f"STEP 5: Zone lookup type: {type(zone_lookup)}")

    merged_data = trip_data.merge(zone_lookup,
            left_on = "PULocationID",
            right_on = "LocationID",
            how = "left"
        )
    print(f"Integration complete: {merged_data.shape[0]} rows, {merged_data.shape[1]} columns")
    return merged_data




if __name__ == "__main__":
    print("Integrating data...")
    merge = intergrate_data()
    print(merge.head())
    print(merge.columns)