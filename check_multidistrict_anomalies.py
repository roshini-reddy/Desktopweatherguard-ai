import pandas as pd

FILE = "data/multidistrict_with_anomalies.csv"

df = pd.read_csv(FILE)

print("=" * 60)
print("MULTI-DISTRICT ANOMALY DISTRIBUTION CHECK")
print("=" * 60)

print("\nRows per district:")
print(df["district"].value_counts().sort_index())

print("\nAnomalies per district:")
anomalies = (
    df[df["anomaly_flag"] == -1]
    .groupby("district")
    .size()
    .sort_values(ascending=False)
)

print(anomalies)

print("\nAnomaly percentage per district:")
district_stats = (
    df.groupby("district")
    .agg(
        total_rows=("anomaly_flag", "size"),
        anomalies=("anomaly_flag", lambda x: (x == -1).sum())
    )
)

district_stats["anomaly_percentage"] = (
    district_stats["anomalies"]
    / district_stats["total_rows"]
    * 100
)

print(district_stats)

print("\nWeather statistics by district:")
print(
    df.groupby("district")[["T2M", "RH2M", "PS"]]
    .mean()
    .round(2)
)

print("\nTemperature range by district:")
print(
    df.groupby("district")["T2M"]
    .agg(["min", "max", "mean", "std"])
    .round(2)
)

print("\n" + "=" * 60)
print("CHECK COMPLETE")
print("=" * 60)