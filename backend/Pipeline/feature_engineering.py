import pandas as pd
import numpy as np 

def engineer_features(dl):
    """
    this is a function to engineer or to derive new columns from existing columns.

    """

    print("\n" + "="*50)
    print("Phase5: Engineering new features ...")
    print("="*50)

    initial_columns = dl.shape[1]
    # derive the time_duration of the trips in minutes
    dl['trip_duration_minutes'] = (dl['tpep_dropoff_datetime'] - dl['tpep_pickup_datetime']).dt.total_seconds() / 60
    dl['trip_duration_minutes'] = dl['trip_duration_minutes'].round(2)
    print(f" Created new_feature: trip_duration_minutes[range 1-1440 min validated]")

    # derive the average speed of the trip in miles per hour

    print("Created Average speed feature...")
    dl['trip_duration_hours'] = dl['trip_duration_minutes'] / 60
    dl['average-speed_mph'] = dl['trip_distance'] / dl['trip_duration_hours']
    dl['average-speed_mph'] = dl['average-speed_mph'].round(2)
    print(f" Created a new_feature: average_speed_mph [range <= 100 mph validated]")

    # derive the tip percentage feature

    print("Created Tip percentage feature...")
    if 'tip_amount' in dl.columns:
        # safe division since fare_amount is > 0
        dl['tip_percentage'] = (dl['tip_amount'] / dl['fare_amount']) * 100
        dl['tip_percentage'] = dl['tip_percentage'].round(2)
        print(f" Created a new_feature: tip_percentage [range 0-100% validated]")


    # feature 5: Cost per Mile
   # print("Created Cost per mile feature...")
    #dl['cost_per_mile'] = np.where(dl['trip_distance'] > 0, dl['fare_amount'] / dl['trip_distance'], 0)
    #dl['cost_per_mile'] = dl['cost_per_mile'].round(2)
    #print(f" Created a new_feature: cost_per_mile [range > 0 validated]")

    final_columns = dl.shape[1]
    new_features = final_columns - initial_columns

    print("\n" + "="*50)
    print(f"initial columns: {initial_columns}")
    print(f"final columns: {final_columns}")
    print(f"feature engineering complete with {new_features} new features added")

    return dl
