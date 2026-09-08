import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

INPUT_FILE = "data/multidistrict_features.csv"
OUTPUT_FILE = "data/multidistrict_with_anomalies.csv"
MODEL_FILE = "isolation_forest_multidistrict.pkl"

# ============================================================
# LOAD FEATURE DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("=" * 60)
print("MULTI-DISTRICT ISOLATION FOREST TRAINING")
print("=" * 60)

print("Rows:", len(df))
print("Districts:", df["district"].nunique())

# ============================================================
# MODEL FEATURES
# ============================================================

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

X = df[feature_cols]

print()
print("Features:", len(feature_cols))
print("Training matrix:", X.shape)

# ============================================================
# TRAIN ISOLATION FOREST
# ============================================================

model = IsolationForest(
    n_estimators=300,
    contamination=0.02,
    random_state=42,
    n_jobs=-1
)

print()
print("Training model...")

model.fit(X)

print("Model trained successfully.")

# ============================================================
# PREDICTIONS
# ============================================================

df["anomaly_flag"] = model.predict(X)

df["anomaly_score"] = model.decision_function(X)

# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 60)
print("ANOMALY RESULTS")
print("=" * 60)

print(
    df["anomaly_flag"]
    .value_counts()
)

print()
print("Anomalies per district:")

print(
    df[df["anomaly_flag"] == -1]
    ["district"]
    .value_counts()
    .sort_index()
)

# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    MODEL_FILE
)

print()
print("Saved model:")
print(MODEL_FILE)

# ============================================================
# SAVE RESULTS
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Saved results:")
print(OUTPUT_FILE)

print()
print("Feature order used by model:")

for i, feature in enumerate(feature_cols, start=1):
    print(f"{i}. {feature}")

print()
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)