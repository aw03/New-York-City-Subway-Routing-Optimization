import pandas as pd

# ---- INPUT FILE PATHS ----
morning_file = "datasets\MTA_Subway_Hourly_Ridership__Oct_21_2024_Morning.csv"   # replace with your actual filename
evening_file = "datasets\MTA_Subway_Hourly_Ridership__Oct_21_2024_Evening.csv"     # replace with your actual filename

# ---- OUTPUT FILE PATHS ----
morning_output = "generated_turnstile_data\MTA_Subway_Aggregated_Ridership_Oct_21_2024_Morning.csv"
evening_output = "generated_turnstile_data\MTA_Subway_Aggregated_Ridership_Oct_21_2024_Evening.csv"

def aggregate_ridership(input_file, output_file):
    df = pd.read_csv(input_file)

    # Force ridership to numeric (removes commas, handles strings)
    df["ridership"] = (
        df["ridership"]
        .astype(str)
        .str.replace(",", "")
        .astype(float)    # or int if you prefer
    )

    # Aggregate
    aggregated_df = (
        df.groupby("station_complex_id", as_index=False)["ridership"].sum()
    )

    aggregated_df.to_csv(output_file, index=False)
    print(f"Saved aggregated file to: {output_file}")

# ---- Run on both datasets ----
aggregate_ridership(morning_file, morning_output)
aggregate_ridership(evening_file, evening_output)
