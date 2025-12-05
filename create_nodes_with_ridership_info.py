import pandas as pd

# ---------- INPUT FILES ----------
nodes_file = "generated_graphs\\nodes.csv"
morning_file = "generated_turnstile_data\\morning_6to10_with_gtfs.csv"
evening_file = "generated_turnstile_data\\evening_4to8_with_gtfs.csv"

# ---------- OUTPUT FILE ----------
nodes_output = "generated_graphs\\nodes_with_ridership.csv"

# ---------- LOAD DATA ----------
nodes = pd.read_csv(nodes_file)
morning = pd.read_csv(morning_file)
evening = pd.read_csv(evening_file)

# ---------- STANDARDIZE GTFS ID TYPES ----------
nodes["stop_id"] = nodes["stop_id"].astype(str)
morning["GTFS Stop ID"] = morning["GTFS Stop ID"].astype(str)
evening["GTFS Stop ID"] = evening["GTFS Stop ID"].astype(str)

# ---------- RENAME RIDERSHIP COLUMNS ----------
morning = morning.rename(columns={"ridership": "ridership_morning"})
evening = evening.rename(columns={"ridership": "ridership_evening"})

# ---------- SELECT ONLY NEEDED COLUMNS ----------
morning_keep = morning[["GTFS Stop ID", "station_complex_id", "ridership_morning"]].drop_duplicates()
evening_keep = evening[["GTFS Stop ID", "ridership_evening"]].drop_duplicates()

# ---------- MERGE MORNING (adds complex_id + morning ridership) ----------
nodes_merged = nodes.merge(
    morning_keep,
    left_on="stop_id",
    right_on="GTFS Stop ID",
    how="left"
)

# ---------- MERGE EVENING ----------
nodes_merged = nodes_merged.merge(
    evening_keep,
    left_on="stop_id",
    right_on="GTFS Stop ID",
    how="left",
)

# ---------- CLEAN UP EXTRA GTFS columns ----------
nodes_merged = nodes_merged.drop(columns=[col for col in nodes_merged.columns if col.startswith("GTFS Stop ID")])

# ---------- SAVE ----------
nodes_merged.to_csv(nodes_output, index=False)
print(f"Saved merged node file → {nodes_output}")

# OPTIONAL: Inspect missing matches
missing = nodes_merged[nodes_merged["station_complex_id"].isna()]
print("\nNodes with no matching complex ID / GTFS mapping (check these):")
print(missing)
