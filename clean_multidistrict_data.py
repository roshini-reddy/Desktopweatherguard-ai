import pandas as pd
import numpy as np

INPUT_FILE = "data/multidistrict_weather.csv"
OUTPUT_FILE = "data/multidistrict_clean.csv"

# Load combined dataset
df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(df["datetime"])

# Sort district-wise by time
df = df.sort_values(
    ["district", "datetime"]
).reset_index(drop=True)

# Convert missing-value markers to NaN
df["T2M"] = df["T2M"].replace(-999, np.nan)
df["RH2M"] = df["RH2M"].replace(-999, np.nan)
df["PS"] = df["PS"].replace(-9990, np.nan)

print("=" * 60)
print("BEFORE CLEANING")
print("=" * 60)

print("\nMissing values:")
print(df.isna().sum())

# Interpolate separately for each district
weather_columns = ["T2M", "RH2M", "PS"]

df[weather_columns] = (
    df.groupby("district")[weather_columns]
    .transform(
        lambda group: group.interpolate(
            method="linear",
            limit_direction="both"
        )
    )
)

print("\n" + "=" * 60)
print("AFTER CLEANING")
print("=" * 60)

print("\nMissing values:")
print(df.isna().sum())

print("\nRows per district:")
print(df["district"].value_counts())

print("\nDate range:")
print("Start:", df["datetime"].min())
print("End:  ", df["datetime"].max())

# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:", OUTPUT_FILE)
print("Total rows:", len(df))