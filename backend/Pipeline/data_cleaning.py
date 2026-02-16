import pandas as pd

"""
phase1: Remove the missing critical values
"""

def remove_missing_values(dl):
    """
    this function will remove the missing rows from the loaded dataset given
    """
    print("Removing missing values ...")
    before_rows = dl.shape[0]

    # Remove rows with missing values in critical columns
    critical_columns = ['PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']
    dl_cleaned = dl.dropna(subset=critical_columns)

    after_rows = dl_cleaned.shape[0]
    print(f"Removed {before_rows - after_rows} rows with missing critical values.")
    return dl_cleaned


"""
 phase2:  Remove Duplicate rows
"""

def remove_duplicates(dl):
    """
    this function will remove the duplicate rows from the loaded data set
    """

    print("Removing the duplicate rows ...")
    before_rows = dl.shape[0]
    dl_cleaned = dl.drop_duplicates()
    after_rows = dl_cleaned.shape[0]
    print(f"Removed {before_rows - after_rows} duplicate rows.")    
    return dl_cleaned


"""
phase3: remove the logical outliers
"""

def remove_outliners(dl):

    """
    this function will remove all the logical inconsistencies in the critical columns
    """

    before_rows = dl.shape[0]
    print("Removing the logical outliers ...")

    excluded_records = []

    # convert datetime first
    dl['tpep_pickup_datetime'] = pd.to_datetime(dl['tpep_pickup_datetime'], errors='coerce')
    dl['tpep_dropoff_datetime'] = pd.to_datetime(dl['tpep_dropoff_datetime'], errors='coerce')

    # Remove invalid datetime conversions 
    mask = dl['tpep_pickup_datetime'].notna() & dl['tpep_dropoff_datetime'].notna()
    excluded_records.append(('Invalid datetiime', (~mask).sum()))
    dl_cleaned = dl[mask].copy()

    # 1. zero/negative trip distance
    mask = dl_cleaned['trip_distance'] > 0
    excluded_records.append(('Zero/Negative trip distance', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 2. zero/negative fare amount 
    mask = dl_cleaned['fare_amount'] > 0
    excluded_records.append(('Zero/Negative fare amount', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 3. Dropoff before pickup
    mask = dl_cleaned['tpep_dropoff_datetime'] >= dl_cleaned['tpep_pickup_datetime']
    excluded_records.append(('Dropoff before pickup', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 4.  Trip duration valdation (1 min to 24 hours) - 
    trip_duration_minutes = (dl_cleaned['tpep_dropoff_datetime'] - dl_cleaned['tpep_pickup_datetime']).dt.total_seconds() / 60
    mask = (trip_duration_minutes >= 1) & (trip_duration_minutes <= 24 * 60)
    excluded_records.append(('Unrealistic trip duration', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 5. Unrealistic distances (> 100 miles)
    mask = dl_cleaned['trip_distance'] <= 100
    excluded_records.append(('Unrealistic trip distance', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 6. Excessive fare amounts (> $500)
    mask = dl_cleaned['fare_amount'] <= 500
    excluded_records.append(('Excessive fare amount', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    # 7. passenger count validation (1 to 6)
    if 'passenger_count' in dl_cleaned.columns:
        mask = dl_cleaned['passenger_count'].between(1, 6)
        excluded_records.append(('Invalid passenger count', (~mask).sum()))
        dl_cleaned = dl_cleaned[mask]

    # 8. Average speed validation (<= 100 mph)
    trip_duration_hours = (
        dl_cleaned['tpep_dropoff_datetime'] - dl_cleaned['tpep_pickup_datetime']
    ).dt.total_seconds() / 3600

    average_speed = dl_cleaned['trip_distance'] / trip_duration_hours
    mask = average_speed <= 100
    excluded_records.append(('Unrealistic average speed', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]
    
    # 9 . Fare component validation

    fare_col = ['extra','mta_tax', 'tip_amount', 'tolls_amount', 'improvement_surcharge', 'congestion_surcharge']

    if 'total_amount' in dl_cleaned.columns:
        # get only the existing columns and fill the NaN with 0
        existing_cols = [c for c in fare_col if c in dl_cleaned.columns]
        dl_cleaned[existing_cols] = dl_cleaned[existing_cols].fillna(0)

        # Remove any negative values in fare components

        all_fare_cols = ['fare_amount', 'total_amount'] + existing_cols
        mask = (dl_cleaned[all_fare_cols] >= 0).all(axis=1)
        excluded_records.append(('Negative values in fare components', (~mask).sum()))
        dl_cleaned = dl_cleaned[mask]

        # validate total_amount consistency

        calculated_total = dl_cleaned[['fare_amount'] + existing_cols].sum(axis=1)
        mask = abs(dl_cleaned['total_amount'] - calculated_total) <= 1.0
        excluded_records.append(('Inconsistent total_amount', (~mask).sum()))
        dl_cleaned = dl_cleaned[mask]


    # 10. cash payment with tips
    if 'payment_type' in dl_cleaned.columns and 'tip_amount' in dl_cleaned.columns:
        mask = ~((dl_cleaned['payment_type'] == 2) & (dl_cleaned['tip_amount'] > 1.0))
        excluded_records.append(('Cash payment with tips', (~mask).sum()))
        dl_cleaned = dl_cleaned[mask]


    # 11. zero distance with significant fare
    mask = ~((dl_cleaned['trip_distance'] == 0) & (dl_cleaned['fare_amount'] > 5))
    excluded_records.append(('Zero distance with significant fare', (~mask).sum()))
    dl_cleaned = dl_cleaned[mask]

    after_rows = dl_cleaned.shape[0]


    # print detailed exclusion log 
    print("Outlier removal summary:")
    print(f"\n{'='*60}")
    print("EXCLUSION LOG:")
    print(f"{'='*60}")
    for reason, count in excluded_records:
        if count > 0:
            print(f"  {reason:.<45} {count:>10,} records")
    print(f"{'='*60}")
    print(f"Total removed: {before_rows - after_rows:,} rows ({((before_rows - after_rows)/before_rows)*100:.2f}%)")
    print(f"Remaining: {after_rows:,} rows")
    print(f"{'='*60}\n")
    
    return dl_cleaned, excluded_records



"""
phase4: standardize the data types
"""

def standardize_data_types(dl):
    """
    this function will standardize the data types of the critical columns
    """

    print("Standardizing data types ...")

    # Convert PULocationID and DOLocationID to integers
    dl['PULocationID'] = dl['PULocationID'].astype(int)
    dl['DOLocationID'] = dl['DOLocationID'].astype(int)

    # Convert trip_distance and fare_amount to floats
    dl['trip_distance'] = dl['trip_distance'].astype(float)
    dl['fare_amount'] = dl['fare_amount'].astype(float)

    # convert other fare components 
    fare_cols = ['extra', 'mta_tax', 'tip_amount', 'tolls_amount', 'total_amount', 'improvement_surcharge', 'congestion_surcharge']
    for col in fare_cols:
        if col in dl.columns:
            dl[col] = dl[col].astype(float)

    # convert integer columns
    int_cols = ['passenger_count', 'payment_type', 'RatecodeID', 'VendorID']
    for col in int_cols:
        if col in dl.columns:
            dl[col] = dl[col].astype(int)



    # Ensure datetime columns are in the datetime format
    datetime_cols = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']
    for col in datetime_cols:
        if col in dl.columns:
            dl[col] = pd.to_datetime(dl[col], errors='coerce')

    print("Data type standardization complete.")
    return dl

# Main function to execute all cleaning steps
def clean_data(dl):
    """
    this function will execute all the cleaning steps in order
    """
    dl = remove_missing_values(dl)
    dl = remove_duplicates(dl)

    # UNPACK the tuple
    dl, exclusion_log = remove_outliners(dl)  
    
    dl = standardize_data_types(dl)
    
    print("\n" + "="*70)
    print("DATA CLEANING COMPLETE")
    print("="*70)
    print(f"Final dataset shape: {dl.shape[0]:,} rows & {dl.shape[1]} columns")
    
    return dl, exclusion_log
