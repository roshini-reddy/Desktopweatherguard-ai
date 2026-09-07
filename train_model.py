import pandas as pd
from sklearn.ensemble import IsolationForest

df = pd.read_csv("data/hyderabad_features.csv")

# these are the columns the model will actually learn from —
# we exclude raw datetime/district (text, not numbers) and the
# intermediate columns we only needed to calculate other features
feature_cols = [
    "T2M", "PS", "RH2M",
    "T2M_diff", "PS_diff", "RH2M_diff",
    "T2M_roll_std", "PS_roll_std", "RH2M_roll_std",
    "T2M_seasonal_zscore", "PS_seasonal_zscore", "RH2M_seasonal_zscore",
]

X = df[feature_cols]


print(X.shape)
print(X.head())

model = IsolationForest(
    n_estimators=200,      # number of trees — more = more stable, slower
    contamination=0.02,    # assume ~2% of readings are anomalies — a starting guess
    random_state=42        # makes results repeatable
)

model.fit(X)

print("Model trained.")

# -1 means the model thinks it's an anomaly, 1 means normal
df["anomaly_flag"] = model.predict(X)

# a continuous score — more negative = more anomalous
df["anomaly_score"] = model.decision_function(X)

print(df["anomaly_flag"].value_counts())
print(df[["datetime", "T2M", "PS", "RH2M", "anomaly_flag", "anomaly_score"]].sort_values("anomaly_score").head(10))
import joblib

joblib.dump(model, "isolation_forest_hyderabad.pkl")
df.to_csv("data/hyderabad_with_anomalies.csv", index=False)

print("Saved model and results.")