import pandas as pd
import numpy as np

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

# ---------- MERGE MORNING ----------
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
    how="left"
)

# ---------- CLEAN UP EXTRA GTFS columns ----------
nodes_merged = nodes_merged.drop(columns=[col for col in nodes_merged.columns if col.startswith("GTFS Stop ID")])

# ---------- ADD NET RIDERSHIP COLUMN ----------
nodes_merged["net_ridership"] = nodes_merged["ridership_morning"] - nodes_merged["ridership_evening"]

# ---------- BALANCE POSITIVE AND NEGATIVE NETS ----------

nodes = nodes_merged.copy()

# nodes = pd.read_csv("nodes_with_ridership.csv")

# If needed:
# nodes["net_ridership"] = nodes["ridership_morning"] - nodes["ridership_evening"]

# 1) Totals
M = nodes["ridership_morning"].sum()

P = nodes["net_ridership"].clip(lower=0).sum()
N = (-nodes["net_ridership"].clip(upper=0)).sum()  # as positive magnitude

alpha_pos = M / P if P > 0 else 0.0
alpha_neg = M / N if N > 0 else 0.0

# 2) Real-valued balanced demand
def scale_net(x):
    if x > 0:
        return alpha_pos * x
    elif x < 0:
        return alpha_neg * x
    else:
        return 0.0

nodes["balanced_real"] = nodes["net_ridership"].apply(scale_net)

# 3) Integerize positives
pos_mask = nodes["balanced_real"] > 0
pos_vals = nodes.loc[pos_mask, "balanced_real"]

pos_floor = np.floor(pos_vals)
pos_frac  = pos_vals - pos_floor

# how many units we still need to add to hit M exactly?
needed_pos = int(M - pos_floor.sum())
needed_pos = max(0, needed_pos)

# give +1 to the nodes with largest fractional parts
pos_indices_sorted = pos_frac.sort_values(ascending=False).index
add_one_pos = pos_indices_sorted[:needed_pos]

pos_int = pos_floor.copy()
pos_int.loc[add_one_pos] += 1

# 4) Integerize negatives (work with absolute values)
neg_mask = nodes["balanced_real"] < 0
neg_vals = -nodes.loc[neg_mask, "balanced_real"]  # magnitude

neg_floor = np.floor(neg_vals)
neg_frac  = neg_vals - neg_floor

needed_neg = int(M - neg_floor.sum())
needed_neg = max(0, needed_neg)

neg_indices_sorted = neg_frac.sort_values(ascending=False).index
add_one_neg = neg_indices_sorted[:needed_neg]

neg_int = neg_floor.copy()
neg_int.loc[add_one_neg] += 1

# 5) Assemble final integer demand
nodes["balanced_net_ridership_int"] = 0

nodes.loc[pos_mask, "balanced_net_ridership_int"] = pos_int.astype(int)
nodes.loc[neg_mask, "balanced_net_ridership_int"] = -neg_int.astype(int)

# 6) Sanity checks
total_pos = nodes["balanced_net_ridership_int"].clip(lower=0).sum()
total_neg = (-nodes["balanced_net_ridership_int"].clip(upper=0)).sum()

print("M (total morning):", M)
print("Total positive int demand:", total_pos)
print("Total negative int demand:", total_neg)

nodes.to_csv("generated_graphs\\nodes_with_balanced_integer_net_ridership.csv", index=False)

# ---------- SAVE ----------
nodes_merged.to_csv(nodes_output, index=False)
print(f"Saved merged node file → {nodes_output}")

# OPTIONAL: Inspect missing matches
missing = nodes_merged[nodes_merged["station_complex_id"].isna()]
print("\nNodes with no matching complex ID / GTFS mapping (check these):")
print(missing)
