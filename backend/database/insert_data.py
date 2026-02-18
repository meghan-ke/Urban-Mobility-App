"""
Insert cleaned data into the database.
Order of insertion matters:
1. rate_codes  (no dependencies)
2. taxi_zones  (no dependencies)
3. trips       (depends on rate_codes and taxi_zones)
"""

import pandas as pd
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parents[1]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from config import PROCESSED_DATA_PATH
from database.db_connection import get_connection, close_connection

def insert_rate_codes(cursor):
    """
    Insert the 6 standard rate codes into the rate_codes table.
    This data is static and does not come from a CSV file.
    """
    print("Inserting rate codes...")

    rate_codes = [
        (1, 'Standard rate',          'Regular metered fare within NYC'),
        (2, 'JFK',                    'Flat rate to/from JFK Airport ($70)'),
        (3, 'Newark',                 'Flat rate to/from Newark Airport'),
        (4, 'Nassau or Westchester',  'Negotiated fare to suburbs outside NYC'),
        (5, 'Negotiated fare',        'Pre-arranged price between driver and passenger'),
        (6, 'Group ride',             'Shared ride with multiple passengers'),
    ]

    for rate_code in rate_codes:
        cursor.execute("""
            INSERT INTO rate_codes (RatecodeID, rate_code_name, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                rate_code_name = VALUES(rate_code_name),
                description = VALUES(description)
        """, rate_code)

    print(f"  {len(rate_codes)} rate codes inserted.")


def insert_taxi_zones(cursor, cleaned_data):
    """
    Insert taxi zone data from the cleaned CSV into the taxi_zones table.
    """
    print("Inserting taxi zones...")

    # Get unique zones from the cleaned data
    zones = cleaned_data[['LocationID', 'Borough', 'Zone', 'service_zone']].drop_duplicates()
    
    count = 0
    for _, row in zones.iterrows():
        cursor.execute("""
            INSERT INTO taxi_zones (LocationID, Borough, Zone, service_zone)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                Borough = VALUES(Borough),
                Zone = VALUES(Zone),
                service_zone = VALUES(service_zone)
        """, (
            int(row['LocationID']), 
            row['Borough'], 
            row['Zone'], 
            row['service_zone']
        ))
        count += 1

    print(f"  {count} taxi zones inserted.")


def insert_trips(cursor, cleaned_data):
    """
    Insert cleaned trip data from the CSV into the trips table.
    """
    print("Inserting trips...")
    print(f"  Total trips to insert: {len(cleaned_data):,}")

    trip_columns = [
        'VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
        'passenger_count', 'trip_distance', 'RatecodeID', 'store_and_fwd_flag',
        'PULocationID', 'DOLocationID', 'payment_type', 'fare_amount',
        'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
        'improvement_surcharge', 'total_amount', 'congestion_surcharge',
        'trip_duration_minutes', 'average_speed_mph', 'tip_percentage'
    ]

    trips = cleaned_data[trip_columns]

    batch_size = 1000
    total_inserted = 0

    for i in range(0, len(trips), batch_size):
        batch = trips.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            cursor.execute("""
                INSERT INTO trips (
                    VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                    passenger_count, trip_distance, RatecodeID, store_and_fwd_flag,
                    PULocationID, DOLocationID, payment_type, fare_amount,
                    extra, mta_tax, tip_amount, tolls_amount,
                    improvement_surcharge, total_amount, congestion_surcharge,
                    trip_duration_minutes, average_speed_mph, tip_percentage
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, tuple(row))
            total_inserted += 1
        
        # Progress indicator
        if (i + batch_size) % 10000 == 0:
            print(f"    Inserted {total_inserted:,} trips so far...")

    print(f"  {total_inserted:,} trips inserted successfully.")


def main():
    print("=" * 60)
    print("Starting data insertion process...")
    print("=" * 60)

    # Load cleaned data
    cleaned_csv_path = project_root / PROCESSED_DATA_PATH
    print(f"\nLoading cleaned data from: {cleaned_csv_path}")
    
    if not cleaned_csv_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_csv_path}")
    
    cleaned_data = pd.read_csv(cleaned_csv_path)
    print(f"Loaded {len(cleaned_data):,} rows from CSV\n")

    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert in correct order (dimensions first, fact table last)
        insert_rate_codes(cursor)
        insert_taxi_zones(cursor, cleaned_data)
        insert_trips(cursor, cleaned_data)

        conn.commit()
        print("\n" + "=" * 60)
        print("All data inserted successfully!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nError during insertion: {e}")
        raise

    finally:
        cursor.close()
        close_connection(conn)


if __name__ == "__main__":
    main()