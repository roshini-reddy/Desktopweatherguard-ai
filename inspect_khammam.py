import pandas as pd

FILE = "data/multidistrict_with_anomalies.csv"

df = pd.read_csv(FILE)

khammam = df[df["district"] == "Khammam"].copy()
anomalies = khammam[khammam["anomaly_flag"] == -1].copy()

print("=" * 70)
print("KHAMMAM ANOMALY INSPECTION")
print("=" * 70)

print("\nTotal Khammam rows:", len(khammam))
print("Khammam anomalies:", len(anomalies))

print("\nAnomaly percentage:")
print(round(len(anomalies) / len(khammam) * 100, 2), "%")

print("\nMost anomalous Khammam observations:")
print(
    anomalies[
        [
            "datetime",
            "T2M",
            "RH2M",
            "PS",
            "T2M_diff",
            "PS_diff",
            "RH2M_diff",
            "T2M_roll_std",
            "PS_roll_std",
            "RH2M_roll_std",
            "T2M_seasonal_zscore",
            "PS_seasonal_zscore",
            "RH2M_seasonal_zscore",
            "anomaly_score",
        ]
    ]
    .sort_values("anomaly_score")
    .head(20)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("ANOMALY SCORE DISTRIBUTION")
print("=" * 70)

print(
    anomalies["anomaly_score"]
    .describe()
)

print("\n" + "=" * 70)
print("AVERAGE FEATURES: NORMAL vs ANOMALY")
print("=" * 70)

feature_cols = [
    "T2M",
    "PS",
    "RH2M",
    "T2M_diff",
    "PS_diff",
    "RH2M_diff",
    "T2M_roll_std",
    "PS_roll_std",
    "RH2M_roll_std",
    "T2M_seasonal_zscore",
    "PS_seasonal_zscore",
    "RH2M_seasonal_zscore",
]

comparison = khammam.groupby("anomaly_flag")[feature_cols].mean()

print(comparison.round(3))

print("\n" + "=" * 70)
print("ANOMALIES BY MONTH")
print("=" * 70)

anomalies["datetime"] = pd.to_datetime(anomalies["datetime"])
print(anomalies["datetime"].dt.month.value_counts().sort_index())

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)