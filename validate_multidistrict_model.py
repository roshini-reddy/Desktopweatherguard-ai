import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

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

    # --------------------------------------------------------
    # Difference features
    # --------------------------------------------------------

    data["T2M_diff"] = (
        data.groupby("district")["T2M"].diff()
    )

    data["PS_diff"] = (
        data.groupby("district")["PS"].diff()
    )

    data["RH2M_diff"] = (
        data.groupby("district")["RH2M"].diff()
    )

    # --------------------------------------------------------
    # Rolling standard deviation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Time features
    # --------------------------------------------------------

    data["hour"] = data["datetime"].dt.hour
    data["month"] = data["datetime"].dt.month

    # --------------------------------------------------------
    # Merge climatology
    # --------------------------------------------------------

    data = data.merge(
        climatology,
        on=["district", "month", "hour"],
        how="left"
    )

    # --------------------------------------------------------
    # Seasonal z-scores
    # --------------------------------------------------------

    for col in ["T2M", "PS", "RH2M"]:

        data[f"{col}_seasonal_zscore"] = (
            data[col] - data[f"{col}_mean"]
        ) / data[f"{col}_std"]

    return data


# ============================================================
# TEST 1 - CLEAN DATA
# ============================================================

print("\n" + "=" * 70)
print("TEST 1: CLEAN DATA")
print("=" * 70)

baseline = create_features(test_df)

baseline = baseline.dropna().reset_index(drop=True)

X_clean = baseline[FEATURES]

baseline_predictions = model.predict(X_clean)

# Convert Isolation Forest:
# -1 = anomaly
#  1 = normal
#
# Our evaluation format:
# 0 = normal
# 1 = anomaly

clean_predictions = (
    baseline_predictions == -1
).astype(int)

clean_total = len(clean_predictions)

clean_anomalies = clean_predictions.sum()

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
# CREATE FAULT DATA
# ============================================================

fault_data = test_df.copy()

# Three independent fault scenarios
spike_data = fault_data.copy()
stuck_data = fault_data.copy()
drift_data = fault_data.copy()

# ============================================================
# SPIKE FAULT
# ============================================================

spike_index = 50

spike_data.loc[
    spike_data.index[spike_index],
    "T2M"
] += 25

# ============================================================
# STUCK SENSOR FAULT
# ============================================================

stuck_start = 50
stuck_end = 60

stuck_temperature = (
    stuck_data.iloc[stuck_start]["T2M"]
)

stuck_data.loc[
    stuck_data.index[stuck_start:stuck_end],
    "T2M"
] = stuck_temperature

# ============================================================
# DRIFT FAULT
# ============================================================

drift_start = 50
drift_end = 65

for i, index in enumerate(
    drift_data.index[drift_start:drift_end]
):

    drift_data.loc[index, "T2M"] += i * 2

# ============================================================
# FUNCTION TO EVALUATE ONE FAULT
# ============================================================

def evaluate_fault(
    name,
    data,
    injected_indexes
):

    features = create_features(data)

    # Keep original datetime before dropping rows
    features = features.dropna().reset_index(drop=True)

    X = features[FEATURES]

    predictions = model.predict(X)

    # Convert:
    # -1 -> 1 anomaly
    #  1 -> 0 normal

    anomaly_predictions = (
        predictions == -1
    ).astype(int)

    # --------------------------------------------------------
    # Match injected readings using datetime
    # --------------------------------------------------------

    injected_datetimes = set(
        data.loc[
            injected_indexes,
            "datetime"
        ]
    )

    actual_labels = (
        features["datetime"]
        .isin(injected_datetimes)
        .astype(int)
        .values
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    tn, fp, fn, tp = confusion_matrix(
        actual_labels,
        anomaly_predictions,
        labels=[0, 1]
    ).ravel()

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    precision = precision_score(
        actual_labels,
        anomaly_predictions,
        zero_division=0
    )

    recall = recall_score(
        actual_labels,
        anomaly_predictions,
        zero_division=0
    )

    f1 = f1_score(
        actual_labels,
        anomaly_predictions,
        zero_division=0
    )

    if (fp + tn) > 0:
        fpr = fp / (fp + tn)
    else:
        fpr = 0

    injected_count = actual_labels.sum()

    detected_count = (
        (
            actual_labels == 1
        )
        &
        (
            anomaly_predictions == 1
        )
    ).sum()

    detection_rate = (
        detected_count / injected_count * 100
        if injected_count > 0
        else 0
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print(name)
    print("-" * 70)

    print(
        "Injected fault readings:",
        injected_count
    )

    print(
        "Detected fault readings:",
        detected_count
    )

    print(
        "Detection rate:",
        round(detection_rate, 2),
        "%"
    )

    print("\nConfusion Matrix:")
    print(
        "TN =", tn,
        "| FP =", fp,
        "| FN =", fn,
        "| TP =", tp
    )

    print(
        "\nPrecision:",
        round(precision * 100, 2),
        "%"
    )

    print(
        "Recall:",
        round(recall * 100, 2),
        "%"
    )

    print(
        "F1-score:",
        round(f1 * 100, 2),
        "%"
    )

    print(
        "False-positive rate:",
        round(fpr * 100, 2),
        "%"
    )

    return {
        "name": name,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "detection_rate": detection_rate / 100,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn
    }


# ============================================================
# TEST 2 - SPIKE
# ============================================================

spike_indexes = [
    spike_index
]

spike_result = evaluate_fault(
    "SPIKE FAULT",
    spike_data,
    spike_indexes
)

# ============================================================
# TEST 3 - STUCK
# ============================================================

stuck_indexes = list(
    stuck_data.index[
        stuck_start:stuck_end
    ]
)

stuck_result = evaluate_fault(
    "STUCK SENSOR FAULT",
    stuck_data,
    stuck_indexes
)

# ============================================================
# TEST 4 - DRIFT
# ============================================================

drift_indexes = list(
    drift_data.index[
        drift_start:drift_end
    ]
)

drift_result = evaluate_fault(
    "DRIFT FAULT",
    drift_data,
    drift_indexes
)

# ============================================================
# OVERALL METRICS
# ============================================================

print("\n" + "=" * 70)
print("OVERALL MODEL PERFORMANCE")
print("=" * 70)

results = [
    spike_result,
    stuck_result,
    drift_result
]

# Average metrics across the three controlled fault tests

overall_precision = np.mean([
    r["precision"]
    for r in results
])

overall_recall = np.mean([
    r["recall"]
    for r in results
])

overall_f1 = np.mean([
    r["f1"]
    for r in results
])

overall_fpr = np.mean([
    r["fpr"]
    for r in results
])

overall_detection = np.mean([
    r["detection_rate"]
    for r in results
])

print(
    "\nPrecision:",
    round(overall_precision * 100, 2),
    "%"
)

print(
    "Recall:",
    round(overall_recall * 100, 2),
    "%"
)

print(
    "F1-score:",
    round(overall_f1 * 100, 2),
    "%"
)

print(
    "False-positive rate:",
    round(overall_fpr * 100, 2),
    "%"
)

print(
    "Overall fault detection rate:",
    round(overall_detection * 100, 2),
    "%"
)

# ============================================================
# FAULT-WISE PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print("FAULT-WISE DETECTION PERFORMANCE")
print("=" * 70)

for result in results:

    print(
        f"{result['name']}:",
        round(
            result["detection_rate"] * 100,
            2
        ),
        "%"
    )

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION SUMMARY")
print("=" * 70)

print(
    "\nClean-data false-positive rate:",
    round(clean_false_positive_rate, 2),
    "%"
)

print(
    "\nOverall Precision:",
    round(overall_precision * 100, 2),
    "%"
)

print(
    "Overall Recall:",
    round(overall_recall * 100, 2),
    "%"
)

print(
    "Overall F1-score:",
    round(overall_f1 * 100, 2),
    "%"
)

print(
    "Overall False-positive rate:",
    round(overall_fpr * 100, 2),
    "%"
)

print(
    "\nSpike detection:",
    round(
        spike_result["detection_rate"] * 100,
        2
    ),
    "%"
)

print(
    "Stuck detection:",
    round(
        stuck_result["detection_rate"] * 100,
        2
    ),
    "%"
)

print(
    "Drift detection:",
    round(
        drift_result["detection_rate"] * 100,
        2
    ),
    "%"
)

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)