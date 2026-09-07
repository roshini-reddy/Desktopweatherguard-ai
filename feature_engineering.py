import pandas as pd

df = pd.read_csv("data/hyderabad_clean.csv")
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)
# how much each reading changed from the one before it (per hour)
df["T2M_diff"] = df["T2M"].diff()
df["PS_diff"] = df["PS"].diff()
df["RH2M_diff"] = df["RH2M"].diff()
window = 6  # 6-hour rolling window

for col in ["T2M", "PS", "RH2M"]:
    df[f"{col}_roll_mean"] = df[col].rolling(window).mean()
    df[f"{col}_roll_std"] = df[col].rolling(window).std()

    df["hour"] = df["datetime"].dt.hour
df["month"] = df["datetime"].dt.month

# for each (month, hour) combo, compute the historical average and spread
climatology = df.groupby(["month", "hour"])[["T2M", "PS", "RH2M"]].agg(["mean", "std"])
climatology.columns = ["_".join(c) for c in climatology.columns]
climatology = climatology.reset_index()
climatology.to_csv("data/hyderabad_climatology.csv", index=False)
print("Saved: data/hyderabad_climatology.csv")
df = df.merge(climatology, on=["month", "hour"], how="left")

# how far is this reading from what's normal for this hour/month, in std-deviation units
for col in ["T2M", "PS", "RH2M"]:
    df[f"{col}_seasonal_zscore"] = (df[col] - df[f"{col}_mean"]) / df[f"{col}_std"]

    df = df.dropna().reset_index(drop=True)

    print(df.head())
print(df.shape)
print(df.columns.tolist())

df.to_csv("data/hyderabad_features.csv", index=False)
print("Saved: data/hyderabad_features.csv")
