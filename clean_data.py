import pandas as pd

df = pd.read_csv("data/hyderabad_weather.csv", skiprows=11)

# combine YEAR/MO/DY/HR into one proper datetime column
df["datetime"] = pd.to_datetime(dict(year=df.YEAR, month=df.MO, day=df.DY, hour=df.HR))
df = df.drop(columns=["YEAR", "MO", "DY", "HR"])

# fix pressure: NASA POWER AG community gives PS in kPa, convert to hPa (standard met unit)
df["PS"] = df["PS"] * 10
import numpy as np

# NASA POWER uses -999 as a fill value for missing data
df["T2M"] = df["T2M"].replace(-999, np.nan)
df["RH2M"] = df["RH2M"].replace(-999, np.nan)
df["PS"] = df["PS"].replace(-9990, np.nan)  # -999 * 10 after our unit conversion

print("Missing values after fixing fill values:")
print(df.isna().sum())

# add district label (useful later when we combine all 8)
df["district"] = "Hyderabad"

# reorder columns nicely
df = df[["datetime", "district", "T2M", "PS", "RH2M"]]

print(df.head())
print(df.shape)
print()
print("Missing values per column:")
print(df.isna().sum())
print()
print("Summary stats:")
print(df.describe())

df = df.sort_values("datetime").reset_index(drop=True)
df[["T2M", "PS", "RH2M"]] = df[["T2M", "PS", "RH2M"]].interpolate(method="linear", limit_direction="both")

print("Missing values after interpolation:")
print(df.isna().sum())

df.to_csv("data/hyderabad_clean.csv", index=False)
print()
print("Saved: data/hyderabad_clean.csv")