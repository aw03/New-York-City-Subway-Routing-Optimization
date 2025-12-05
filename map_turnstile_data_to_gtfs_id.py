import pandas as pd

# ---------- INPUT FILES ----------
morning_file = "generated_turnstile_data\MTA_Subway_Aggregated_Ridership_Oct_21_2024_Morning.csv"   # has station_complex_id, ridership
evening_file = "generated_turnstile_data\MTA_Subway_Aggregated_Ridership_Oct_21_2024_Evening.csv"    # has station_complex_id, ridership
station_map_file = "datasets\MTA_Subway_Stations_20251204.csv"  # has 'Complex ID', 'GTFS Stop ID', etc.

# ---------- OUTPUT FILES ----------
morning_output = "generated_turnstile_data\morning_6to10_with_gtfs.csv"
evening_output = "generated_turnstile_data\evening_4to8_with_gtfs.csv"

# ---------- LOAD DATA ----------
morning = pd.read_csv(morning_file)
evening = pd.read_csv(evening_file)
stations = pd.read_csv(station_map_file)

# Make sure IDs are comparable types (convert to int or str consistently)
# Here we'll use int; switch to str if your station_complex_id is not numeric.
morning["station_complex_id"] = morning["station_complex_id"].astype(int)
evening["station_complex_id"] = evening["station_complex_id"].astype(int)
stations["Complex ID"] = stations["Complex ID"].astype(int)

# Keep just the mapping columns and drop duplicates just in case
id_mapping = stations[["Complex ID", "GTFS Stop ID"]].drop_duplicates()

# ---------- MERGE GTFS IDS INTO RIDERSHIP DATA ----------
morning_with_gtfs = morning.merge(
    id_mapping,
    left_on="station_complex_id",
    right_on="Complex ID",
    how="left"
)

evening_with_gtfs = evening.merge(
    id_mapping,
    left_on="station_complex_id",
    right_on="Complex ID",
    how="left"
)

# Optionally drop the extra 'Complex ID' column after the merge
morning_with_gtfs = morning_with_gtfs.drop(columns=["Complex ID"])
evening_with_gtfs = evening_with_gtfs.drop(columns=["Complex ID"])

# ---------- SAVE RESULTS ----------
morning_with_gtfs.to_csv(morning_output, index=False)
evening_with_gtfs.to_csv(evening_output, index=False)

print(f"Saved: {morning_output}")
print(f"Saved: {evening_output}")

# ---------- OPTIONAL: CHECK ANY STATIONS THAT DIDN'T MATCH ----------
missing_morning = morning_with_gtfs[morning_with_gtfs["GTFS Stop ID"].isna()]
missing_evening = evening_with_gtfs[evening_with_gtfs["GTFS Stop ID"].isna()]

print("\nMorning rows with missing GTFS ID:")
print(missing_morning)

print("\nEvening rows with missing GTFS ID:")
print(missing_evening)
