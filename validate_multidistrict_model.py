import pandas as pd
import numpy as np
import joblib

# ============================================================
# CONFIGURATION
# ============================================================

DATA_FILE = "data/multidistrict_clean.csv"
CLIMATOLOGY_FILE = "data/multidistrict_climatology.csv"
MODEL_FILE = "isolation_forest_multidistrict.pkl"

FEATURES = [
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

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("WEATHERGUARD AI - MULTI-DISTRICT MODEL VALIDATION")
print("=" * 70)

df = pd.read_csv(DATA_FILE)
df["datetime"] = pd.to_datetime(df["datetime"])

climatology = pd.read_csv(CLIMATOLOGY_FILE)

model = joblib.load(MODEL_FILE)

print("\nLoaded data:", len(df), "rows")
print("Districts:", df["district"].nunique())
print("Model loaded successfully.")

# ============================================================
# SELECT CLEAN TEST DATA
# ============================================================

# Use a continuous section from each district.
# We intentionally use clean historical data before injecting faults.

test_parts = []

for district in df["district"].unique():

    district_df = df[df["district"] == district].copy()

    # Select 100 consecutive rows from the middle
    start = len(district_df) // 2
    sample = district_df.iloc[start:start + 100].copy()

    test_parts.append(sample)

test_df = pd.concat(test_parts, ignore_index=True)

print("\nValidation rows:", len(test_df))

# ============================================================
# FEATURE GENERATION FUNCTION
# ============================================================

def create_features(data):

    data = data.copy()

    data = data.sort_values(
        ["district", "datetime"]
    ).reset_index(drop=True)

    # Differences
    data["T2M_diff"] = (
        data.groupby("district")["T2M"].diff()
    )

    data["PS_diff"] = (
        data.groupby("district")["PS"].diff()
    )

    data["RH2M_diff"] = (
        data.groupby("district")["RH2M"].diff()
    )

    # Rolling standard deviation
    for col in ["T2M", "PS", "RH2M"]:

        data[f"{col}_roll_std"] = (
            data.groupby("district")[col]
            .transform(
                lambda x: x.rolling(
                    6,
                    min_periods=6
                ).std()
            )
        )

    # Time features
    data["hour"] = data["datetime"].dt.hour
    data["month"] = data["datetime"].dt.month

    # Merge district-specific climatology
    data = data.merge(
        climatology,
        on=["district", "month", "hour"],
        how="left"
    )

    # Seasonal z-scores
    for col in ["T2M", "PS", "RH2M"]:

        data[f"{col}_seasonal_zscore"] = (
            data[col] - data[f"{col}_mean"]
        ) / data[f"{col}_std"]

    return data


# ============================================================
# BASELINE TEST
# ============================================================

print("\n" + "=" * 70)
print("TEST 1: CLEAN DATA")
print("=" * 70)

baseline = create_features(test_df)

baseline = baseline.dropna().reset_index(drop=True)

X_clean = baseline[FEATURES]

baseline_predictions = model.predict(X_clean)

clean_anomalies = (baseline_predictions == -1).sum()
clean_total = len(baseline_predictions)

clean_false_positive_rate = (
    clean_anomalies / clean_total * 100
)

print("\nClean test rows:", clean_total)
print("False anomalies:", clean_anomalies)
print(
    "False-positive rate:",
    round(clean_false_positive_rate, 2),
    "%"
)

# ============================================================
# FAULT INJECTION DATA
# ============================================================

fault_data = test_df.copy()

# Make three separate copies
spike_data = fault_data.copy()
stuck_data = fault_data.copy()
drift_data = fault_data.copy()

# ------------------------------------------------------------
# SPIKE
# ------------------------------------------------------------

# Inject a very sudden temperature spike
spike_index = 50

district = spike_data.iloc[spike_index]["district"]

spike_data.loc[
    spike_data.index[spike_index],
    "T2M"
] += 25

# ------------------------------------------------------------
# STUCK SENSOR
# ------------------------------------------------------------

# Force temperature to remain exactly constant
stuck_start = 50
stuck_end = 60

stuck_temperature = stuck_data.iloc[stuck_start]["T2M"]

stuck_data.loc[
    stuck_data.index[stuck_start:stuck_end],
    "T2M"
] = stuck_temperature

# ------------------------------------------------------------
# DRIFT
# ------------------------------------------------------------

# Gradually increase temperature
drift_start = 50
drift_end = 65

for i, index in enumerate(
    drift_data.index[drift_start:drift_end]
):

    drift_data.loc[index, "T2M"] += i * 2

# ============================================================
# FUNCTION TO TEST A FAULT
# ============================================================

def evaluate_fault(name, data, injected_indexes):

    features = create_features(data)

    features = features.dropna().reset_index(drop=True)

    X = features[FEATURES]

    predictions = model.predict(X)

    # Find whether the injected region contains
    # at least one ML anomaly.
    detected = False

    for original_index in injected_indexes:

        matching = features[
            features["datetime"]
            == data.loc[original_index, "datetime"]
        ]

        if len(matching) > 0:

            row_index = matching.index[0]

            if predictions[row_index] == -1:
                detected = True

    anomaly_count = (predictions == -1).sum()

    print("\n" + "-" * 70)
    print(name)
    print("-" * 70)

    print("Injected readings:", len(injected_indexes))
    print("Detected by Isolation Forest:", detected)
    print("Total anomalies in test:", anomaly_count)

    return detected


# ============================================================
# TEST 2 - SPIKE
# ============================================================

spike_detected = evaluate_fault(
    "SPIKE FAULT",
    spike_data,
    [spike_index]
)

# ============================================================
# TEST 3 - STUCK
# ============================================================

stuck_indexes = list(
    stuck_data.index[stuck_start:stuck_end]
)

stuck_detected = evaluate_fault(
    "STUCK SENSOR FAULT",
    stuck_data,
    stuck_indexes
)

# ============================================================
# TEST 4 - DRIFT
# ============================================================

drift_indexes = list(
    drift_data.index[drift_start:drift_end]
)

drift_detected = evaluate_fault(
    "DRIFT FAULT",
    drift_data,
    drift_indexes
)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

print(
    "\nClean-data false-positive rate:",
    round(clean_false_positive_rate, 2),
    "%"
)

print(
    "Spike detected:",
    "YES" if spike_detected else "NO"
)

print(
    "Stuck detected:",
    "YES" if stuck_detected else "NO"
)

print(
    "Drift detected:",
    "YES" if drift_detected else "NO"
)

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)