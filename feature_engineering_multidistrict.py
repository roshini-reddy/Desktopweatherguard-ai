import pandas as pd
import numpy as np

INPUT_FILE = "data/multidistrict_clean.csv"
OUTPUT_FILE = "data/multidistrict_features.csv"
CLIMATOLOGY_FILE = "data/multidistrict_climatology.csv"

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(df["datetime"])

df = df.sort_values(
    ["district", "datetime"]
).reset_index(drop=True)

print("=" * 60)
print("MULTI-DISTRICT FEATURE ENGINEERING")
print("=" * 60)

print("Input rows:", len(df))
print("Districts:", df["district"].nunique())

# ============================================================
# TIME FEATURES
# ============================================================

df["hour"] = df["datetime"].dt.hour
df["month"] = df["datetime"].dt.month

# ============================================================
# DIFFERENCE FEATURES
# Calculate separately for each district
# ============================================================

df["T2M_diff"] = (
    df.groupby("district")["T2M"]
    .diff()
)

df["PS_diff"] = (
    df.groupby("district")["PS"]
    .diff()
)

df["RH2M_diff"] = (
    df.groupby("district")["RH2M"]
    .diff()
)

# ============================================================
# ROLLING FEATURES
# 6-hour rolling standard deviation
# calculated separately for each district
# ============================================================

window = 6

for col in ["T2M", "PS", "RH2M"]:

    df[f"{col}_roll_mean"] = (
        df.groupby("district")[col]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=window
            ).mean()
        )
    )

    df[f"{col}_roll_std"] = (
        df.groupby("district")[col]
        .transform(
            lambda x: x.rolling(
                window,
                min_periods=window
            ).std()
        )
    )

# ============================================================
# DISTRICT-SPECIFIC CLIMATOLOGY
# ============================================================

climatology = (
    df.groupby(
        ["district", "month", "hour"]
    )[["T2M", "PS", "RH2M"]]
    .agg(["mean", "std"])
)

# Flatten multi-level column names
climatology.columns = [
    "_".join(column)
    for column in climatology.columns
]

climatology = climatology.reset_index()

# Avoid division by zero
for col in [
    "T2M_std",
    "PS_std",
    "RH2M_std"
]:
    climatology[col] = climatology[col].replace(0, np.nan)

climatology.to_csv(
    CLIMATOLOGY_FILE,
    index=False
)

print()
print("Saved climatology:")
print(CLIMATOLOGY_FILE)

# ============================================================
# MERGE CLIMATOLOGY
# ============================================================

df = df.merge(
    climatology,
    on=["district", "month", "hour"],
    how="left"
)

# ============================================================
# SEASONAL Z-SCORES
# ============================================================

df["T2M_seasonal_zscore"] = (
    (df["T2M"] - df["T2M_mean"])
    / df["T2M_std"]
)

df["PS_seasonal_zscore"] = (
    (df["PS"] - df["PS_mean"])
    / df["PS_std"]
)

df["RH2M_seasonal_zscore"] = (
    (df["RH2M"] - df["RH2M_mean"])
    / df["RH2M_std"]
)

# ============================================================
# CLEAN FEATURE DATA
# ============================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.dropna().reset_index(drop=True)

# ============================================================
# CHECK RESULTS
# ============================================================

print()
print("=" * 60)
print("FEATURE ENGINEERING COMPLETE")
print("=" * 60)

print("Rows after feature engineering:", len(df))

print()
print("Rows per district:")

print(
    df["district"]
    .value_counts()
    .sort_index()
)

print()
print("Missing values:")
print(
    df.isna().sum()
)

print()
print("Feature columns:")
print(
    df.columns.tolist()
)

# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved:", OUTPUT_FILE)