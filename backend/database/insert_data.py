"""
Insert cleaned data into the database.
Handles NaN values and foreign key constraints.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parents[1]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from config import PROCESSED_DATA_PATH
from database.db_connection import get_connection, close_connection


def insert_rate_codes(cursor):
    """Insert the 6 standard rate codes."""
    print("Inserting rate codes...")

    rate_codes = [
        (1, 'Standard rate', 'Regular metered fare within NYC'),
        (2, 'JFK', 'Flat rate to/from JFK Airport ($70)'),
        (3, 'Newark', 'Flat rate to/from Newark Airport'),
        (4, 'Nassau or Westchester', 'Negotiated fare to suburbs outside NYC'),
        (5, 'Negotiated fare', 'Pre-arranged price between driver and passenger'),
        (6, 'Group ride', 'Shared ride with multiple passengers'),
    ]

    for rate_code in rate_codes:
        cursor.execute("""
            INSERT INTO rate_codes (RatecodeID, rate_code_name, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                rate_code_name = VALUES(rate_code_name)
        """, rate_code)

    print(f"  ✓ {len(rate_codes)} rate codes inserted.")


def insert_taxi_zones_chunked(cursor, csv_path):
    """Insert taxi zones by reading CSV in chunks."""
    print("Inserting taxi zones...")
    
    zones_seen = set()
    zone_count = 0
    skipped = 0
    
    for chunk in pd.read_csv(csv_path, chunksize=50000, 
                             usecols=['LocationID', 'Borough', 'Zone', 'service_zone']):
        
        # Drop rows where Zone is null (required field)
        chunk = chunk.dropna(subset=['Zone'])
        
        # Replace remaining NaN with None
        chunk = chunk.replace({np.nan: None})
        
        zones = chunk[['LocationID', 'Borough', 'Zone', 'service_zone']].drop_duplicates()
        
        for _, row in zones.iterrows():
            location_id = int(row['LocationID'])
            
            if location_id in zones_seen:
                continue
            
            # Double-check Zone is not None
            if pd.isna(row['Zone']) or row['Zone'] is None:
                skipped += 1
                continue
            
            cursor.execute("""
                INSERT INTO taxi_zones (LocationID, Borough, Zone, service_zone)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    Borough = VALUES(Borough)
            """, (location_id, row['Borough'], row['Zone'], row['service_zone']))
            
            zones_seen.add(location_id)
            zone_count += 1

    if skipped > 0:
        print(f"  Skipped {skipped} zone with missing Zone values")
    print(f"  ✓ {zone_count} taxi zones inserted.")


def insert_trips_chunked(cursor, conn, csv_path):
    """Insert trips by reading CSV in chunks."""
    print("Inserting trips in batches...")
    
    # Get valid LocationIDs once
    print("  Loading valid LocationIDs from taxi_zones...")
    cursor.execute("SELECT LocationID FROM taxi_zones")
    valid_location_ids = {row[0] for row in cursor.fetchall()}
    print(f"  Found {len(valid_location_ids)} valid zones")
   
    cursor.execute("SELECT RatecodeID FROM rate_codes")
    valid_rate_codes = {row[0] for row in cursor.fetchall()}
    print(f"  Found {len(valid_rate_codes)} valid rate codes")
    

    trip_columns = [
        'VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
        'passenger_count', 'trip_distance', 'RatecodeID', 'store_and_fwd_flag',
        'PULocationID', 'DOLocationID', 'payment_type', 'fare_amount',
        'extra', 'mta_tax', 'tip_amount', 'tolls_amount',
        'improvement_surcharge', 'total_amount', 'congestion_surcharge',
        'trip_duration_minutes', 'average-speed_mph', 'tip_percentage'
    ]
    
    chunk_size = 10000
    total_inserted = 0
    total_skipped = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size, 
                                                    usecols=trip_columns), 1):
        
        # Drop rows with missing required fields
        chunk = chunk.dropna(subset=['tpep_pickup_datetime', 'tpep_dropoff_datetime'])
        
        # Filter out invalid LocationIDs
        initial_count = len(chunk)
        chunk = chunk[
            chunk['PULocationID'].isin(valid_location_ids) & 
            chunk['DOLocationID'].isin(valid_location_ids) &
            (chunk['RatecodeID'].isin(valid_rate_codes) | chunk['RatecodeID'].isna())
        ]
        skipped_in_chunk = initial_count - len(chunk)
        total_skipped += skipped_in_chunk

         # Replace infinite values first
        chunk['tip_percentage'] = chunk['tip_percentage'].replace(
            [np.inf, -np.inf], np.nan
        )

         # Cap unrealistic percentages (0% to 100%)
        chunk['tip_percentage'] = chunk['tip_percentage'].clip(lower=0, upper=100)

        # Replace remaining NaN with None
        chunk = chunk.replace({np.nan: None})
        
        # Rename column to match database
        chunk = chunk.rename(columns={'average-speed_mph': 'average_speed_mph'})
        
        # Prepare batch insert
        values = []
        for _, row in chunk.iterrows():
            values.append(tuple(row))
        
        if not values:
            continue
        
        # Batch insert
        cursor.executemany("""
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
        """, values)
        
        total_inserted += len(values)
        
        # Commit every 50k rows
        if chunk_num % 5 == 0:
            conn.commit()
            print(f"    Progress: {total_inserted:,} trips inserted, {total_skipped:,} skipped...")
    
    conn.commit()
    if total_skipped > 0:
        print(f"  Skipped {total_skipped:,} trips with invalid locationIDs")
    print(f"  ✓ {total_inserted:,} trips inserted successfully.")


def main():
    print("=" * 60)
    print("Starting data insertion process...")
    print("=" * 60)

    csv_path = project_root / PROCESSED_DATA_PATH
    print(f"\nCSV Path: {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        insert_rate_codes(cursor)
        conn.commit()
        
        insert_taxi_zones_chunked(cursor, csv_path)
        conn.commit()
        
        insert_trips_chunked(cursor, conn, csv_path)

        print("\n" + "=" * 60)
        print("✓ All data inserted successfully!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error: {e}")
        raise

    finally:
        cursor.close()
        close_connection(conn)


if __name__ == "__main__":
    main()
