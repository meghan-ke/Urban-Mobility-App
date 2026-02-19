# """
# Integrating the trip data with the zone lookup data.
# """

from datetime import datetime
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

def save_exclusion_log(exclusion_log):
    #Save excluded records to CSV in logs directory
    if not exclusion_log:
        print("No exclusions to log.")
        return
    
    log_dir = project_root / LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"data_exclusions_{timestamp}.csv"
    
    # Convert list of tuples to DataFrame
    log_df = pd.DataFrame(exclusion_log, columns=['reason', 'count'])
    log_df.to_csv(log_file, index=False)
    
    print(f"✓ Exclusion log saved: {log_file}")
    print(f"  Total exclusion reasons: {len(exclusion_log)}")


def intergrate_data():
    
    """
    this function merges the two data sets together using the PULocationID.
    """

    print("Integrating datasets ...")

    trip_data = load_trip_data()

    print(f"STEP 2: Type of trip_data AFTER load: {type(trip_data)}")
    
    print("STEP 3: About to call clean_data...")
    
    trip_data, exclusion_log = clean_data(trip_data)
    save_exclusion_log(exclusion_log)
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