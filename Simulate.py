import joblib

model = joblib.load("isolation_forest_hyderabad.pkl")

print("Model loaded successfully!")

import pandas as pd

# Load historical Hyderabad data
historical = pd.read_csv("data/hyderabad_clean.csv")

historical["datetime"] = pd.to_datetime(historical["datetime"])
historical = historical.sort_values("datetime").reset_index(drop=True)

print("Historical data loaded:", historical.shape)

simulated_data = pd.DataFrame({
    "datetime": pd.to_datetime([
        "2026-09-07 10:00:00",
        "2026-09-07 11:00:00",
        "2026-09-07 12:00:00",
        "2026-09-07 13:00:00",
        "2026-09-07 14:00:00"
    ]),
    "T2M": [32.5, 45.0, 31.8, 32.1, 10.0],
    "PS": [1008, 900, 1007, 1008, 1005],
    "RH2M": [55, 20, 56, 55, 95]
})

print("\nSimulated NEW data:")
print(simulated_data)
print("Number of features expected:", model.n_features_in_)
combined = pd.concat(
    [historical, simulated_data],
    ignore_index=True
)

combined = combined.sort_values("datetime").reset_index(drop=True)

print("\nCombined data shape:", combined.shape)
# STEP 8: Calculate change from the previous reading

combined["T2M_diff"] = combined["T2M"].diff()
combined["PS_diff"] = combined["PS"].diff()
combined["RH2M_diff"] = combined["RH2M"].diff()

print("\nDiff features created!")

print(
    combined[
        ["datetime", "T2M", "PS", "RH2M",
         "T2M_diff", "PS_diff", "RH2M_diff"]
    ].tail(10)
)
# STEP 9: Calculate 6-hour rolling standard deviation

window = 6

for col in ["T2M", "PS", "RH2M"]:
    combined[f"{col}_roll_std"] = combined[col].rolling(window).std()

print("\nRolling standard deviation features created!")

print(
    combined[
        ["datetime",
         "T2M_roll_std",
         "PS_roll_std",
         "RH2M_roll_std"]
    ].tail(10)
)
# STEP 10: Add seasonal z-score features

climatology = pd.read_csv("data/hyderabad_climatology.csv")

print("\nClimatology loaded:")
print(climatology.head())
combined["hour"] = combined["datetime"].dt.hour
combined["month"] = combined["datetime"].dt.month

print("\nMonth and hour created!")
print(combined[["datetime", "month", "hour"]].tail(10))
combined = combined.merge(
    climatology,
    on=["month", "hour"],
    how="left"
)

print("\nClimatology merged!")

print(
    combined[
        ["datetime",
         "T2M", "T2M_mean", "T2M_std",
         "PS", "PS_mean", "PS_std",
         "RH2M", "RH2M_mean", "RH2M_std"]
    ].tail(10)
)
for col in ["T2M", "PS", "RH2M"]:
    combined[f"{col}_seasonal_zscore"] = (
        (combined[col] - combined[f"{col}_mean"])
        / combined[f"{col}_std"]
    )

print("\nSeasonal z-score features created!")

print(
    combined[
        ["datetime",
         "T2M_seasonal_zscore",
         "PS_seasonal_zscore",
         "RH2M_seasonal_zscore"]
    ].tail(10)
)
# STEP 11: Select the exact features expected by the model

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
    "RH2M_seasonal_zscore"
]

# Select only the simulated/new rows
new_data = combined[
    combined["datetime"].isin(simulated_data["datetime"])
].copy()

# Create the input matrix for the model
X_new = new_data[feature_cols]

print("\nFeatures selected for new data:")
print(X_new)

print("\nShape of X_new:", X_new.shape)
print("Number of features:", X_new.shape[1])
# STEP 12: Predict anomalies for the new simulated data

prediction = model.predict(X_new)
anomaly_score = model.decision_function(X_new)

print("\nPrediction results:")

for i in range(len(new_data)):
    if prediction[i] == -1:
        status = "ANOMALY"
    else:
        status = "NORMAL"

    print(
        new_data.iloc[i]["datetime"],
        "→",
        status,
        "| Score:",
        anomaly_score[i]
    )
    
