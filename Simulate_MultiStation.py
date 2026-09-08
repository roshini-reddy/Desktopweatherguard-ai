import os
import time
import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SECONDS_PER_READING = 5
TOTAL_READINGS = 24

MODEL_FILE = "isolation_forest_multidistrict.pkl"
CLEAN_DATA_FILE = "data/multidistrict_clean.csv"
CLIMATOLOGY_FILE = "data/multidistrict_climatology.csv"
OUTPUT_FILE = "data/multistation_simulated_results.csv"

DISTRICTS = [
    "Hyderabad",
    "Medak",
    "Sangareddy",
    "Hanamkonda",
    "Nizamabad",
    "Karimnagar",
    "Khammam",
    "Mahbubnagar",
]


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
# FAULT PLAN
# ============================================================
#
# Different stations receive different faults so that the
# dashboard can demonstrate the complete system.
#
# SPIKE  -> Sangareddy
# STUCK  -> Nizamabad
# DRIFT  -> Khammam
#
# Other stations remain normal.
# ============================================================

FAULT_PLAN = {
    "Sangareddy": "SPIKE",
    "Nizamabad": "STUCK",
    "Khammam": "DRIFT",
}


# ============================================================
# LOAD MODEL AND DATA
# ============================================================

print("=" * 70)
print("WEATHERGUARD AI - MULTI-STATION LIVE SIMULATOR")
print("=" * 70)

print("\nLoading model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")

print("\nLoading historical weather data...")

historical = pd.read_csv(CLEAN_DATA_FILE)
historical["datetime"] = pd.to_datetime(historical["datetime"])

print("Historical rows:", len(historical))

print("\nLoading climatology...")

climatology = pd.read_csv(CLIMATOLOGY_FILE)

print("Climatology loaded successfully.")


# ============================================================
# PREPARE SIMULATION
# ============================================================

# Remove old simulation output
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

print("\nPrevious simulation file removed.")

# Store generated readings for each station
station_history = {}

# Last historical timestamp for each district
last_times = {}

for district in DISTRICTS:

    district_data = historical[
        historical["district"].str.lower()
        == district.lower()
    ].copy()

    district_data = district_data.sort_values("datetime")

    last_times[district] = district_data["datetime"].iloc[-1]

    station_history[district] = []

print("\nSimulation stations:")

for district in DISTRICTS:

    fault = FAULT_PLAN.get(district, "NONE")

    print(
        f"  {district:<15} -> {fault}"
    )


# ============================================================
# HELPER: GET EXPECTED WEATHER
# ============================================================

def get_expected_weather(district, timestamp):

    month = timestamp.month
    hour = timestamp.hour

    row = climatology[
        (climatology["district"].str.lower() == district.lower())
        & (climatology["month"] == month)
        & (climatology["hour"] == hour)
    ]

    if row.empty:
        return None

    row = row.iloc[0]

    return {
        "T2M": row["T2M_mean"],
        "RH2M": row["RH2M_mean"],
        "PS": row["PS_mean"],
    }


# ============================================================
# HELPER: GENERATE NORMAL WEATHER
# ============================================================

def generate_normal_weather(district, timestamp):

    expected = get_expected_weather(
        district,
        timestamp
    )

    if expected is None:
        return None

    # Small realistic random variation
    temperature = expected["T2M"] + np.random.normal(0, 0.8)
    humidity = expected["RH2M"] + np.random.normal(0, 2.0)
    pressure = expected["PS"] + np.random.normal(0, 0.8)

    # Keep values physically reasonable
    humidity = np.clip(humidity, 5, 100)

    return {
        "T2M": round(temperature, 2),
        "RH2M": round(humidity, 2),
        "PS": round(pressure, 2),
    }


# ============================================================
# FAULT INJECTION
# ============================================================

def apply_fault(
    district,
    reading_index,
    reading,
    previous_reading
):

    fault = FAULT_PLAN.get(
        district,
        "NONE"
    )

    # --------------------------------------------------------
    # SPIKE
    # --------------------------------------------------------

    if fault == "SPIKE":

        # Inject a large temperature spike at reading 5
        if reading_index == 5:

            reading["T2M"] += 25

    # --------------------------------------------------------
    # STUCK
    # --------------------------------------------------------

    elif fault == "STUCK":

        # Keep temperature constant from readings 10-14
        if 10 <= reading_index <= 14:

            if previous_reading is not None:

                reading["T2M"] = previous_reading["T2M"]

    # --------------------------------------------------------
    # DRIFT
    # --------------------------------------------------------

    elif fault == "DRIFT":

        # Gradually increase temperature from reading 17
        if reading_index >= 17:

            drift_amount = (
                reading_index - 16
            ) * 2

            reading["T2M"] += drift_amount

    return reading


# ============================================================
# FAULT DETECTION
# ============================================================

def detect_spike(
    current,
    previous,
    expected_temperature
):

    if previous is None:
        return False

    temperature_change = abs(
        current["T2M"]
        - previous["T2M"]
    )

    deviation = abs(
        current["T2M"]
        - expected_temperature
    )

    if (
        temperature_change >= 10
        and deviation >= 8
    ):
        return True

    return False


def detect_stuck(history):

    if len(history) < 4:
        return False

    recent = [
        row["T2M"]
        for row in history[-4:]
    ]

    temperature_range = (
        max(recent) - min(recent)
    )

    return temperature_range < 0.01


def detect_drift(
    history,
    expected_temperature
):

    if len(history) < 4:
        return False

    recent = [
        row["T2M"]
        for row in history[-4:]
    ]

    increasing = (
        recent[0]
        < recent[1]
        < recent[2]
        < recent[3]
    )

    decreasing = (
        recent[0]
        > recent[1]
        > recent[2]
        > recent[3]
    )

    deviation = abs(
        recent[-1]
        - expected_temperature
    )

    if (
        (increasing or decreasing)
        and deviation >= 5
    ):
        return True

    return False


# ============================================================
# FEATURE CREATION
# ============================================================

def create_features_for_station(
    district,
    simulated_rows
):

    historical_station = historical[
        historical["district"].str.lower()
        == district.lower()
    ].copy()

    combined = pd.concat(
        [
            historical_station,
            pd.DataFrame(simulated_rows)
        ],
        ignore_index=True
    )

    combined["datetime"] = pd.to_datetime(
        combined["datetime"]
    )

    combined = combined.sort_values(
        "datetime"
    ).reset_index(drop=True)

    # Differences
    combined["T2M_diff"] = (
        combined["T2M"].diff()
    )

    combined["PS_diff"] = (
        combined["PS"].diff()
    )

    combined["RH2M_diff"] = (
        combined["RH2M"].diff()
    )

    # Rolling standard deviation
    for col in [
        "T2M",
        "PS",
        "RH2M"
    ]:

        combined[
            f"{col}_roll_std"
        ] = (
            combined[col]
            .rolling(6)
            .std()
        )

    # Time features
    combined["hour"] = (
        combined["datetime"].dt.hour
    )

    combined["month"] = (
        combined["datetime"].dt.month
    )

    # Climatology
    combined = combined.merge(
        climatology,
        on=[
            "district",
            "month",
            "hour"
        ],
        how="left"
    )

    # Seasonal z-scores
    for col in [
        "T2M",
        "PS",
        "RH2M"
    ]:

        combined[
            f"{col}_seasonal_zscore"
        ] = (
            combined[col]
            - combined[f"{col}_mean"]
        ) / combined[f"{col}_std"]

    return combined


# ============================================================
# LIVE SIMULATION
# ============================================================

result_rows = []

print("\n")
print("=" * 70)
print("STARTING LIVE SIMULATION")
print("=" * 70)

for reading_index in range(
    TOTAL_READINGS
):

    print(
        f"\nREADING {reading_index + 1}"
        f"/{TOTAL_READINGS}"
    )

    for district in DISTRICTS:

        # Create next timestamp
        timestamp = (
            last_times[district]
            + pd.Timedelta(
                hours=reading_index + 1
            )
        )

        # Generate normal reading
        weather = generate_normal_weather(
            district,
            timestamp
        )

        if weather is None:
            continue

        # Previous simulated reading
        previous = None

        if station_history[district]:

            previous = station_history[
                district
            ][-1]

        # Apply synthetic fault
        weather = apply_fault(
            district,
            reading_index,
            weather,
            previous
        )

        # Store timestamp/district
        current = {
            "datetime": timestamp,
            "district": district,
            "T2M": round(
                weather["T2M"],
                2
            ),
            "PS": round(
                weather["PS"],
                2
            ),
            "RH2M": round(
                weather["RH2M"],
                2
            ),
        }

        # Add to station history
        station_history[
            district
        ].append(current)

        # ----------------------------------------------------
        # ML FEATURES
        # ----------------------------------------------------

        feature_data = (
            create_features_for_station(
                district,
                station_history[district]
            )
        )

        current_features = (
            feature_data.iloc[-1]
        )

        X = pd.DataFrame(
            [
                current_features[FEATURES]
            ]
        )

        # Safety check
        if X.isna().any().any():

            ml_status = "NORMAL"
            anomaly_score = 0.0

        else:

            prediction = model.predict(X)[0]

            anomaly_score = float(
                model.decision_function(X)[0]
            )

            ml_status = (
                "ANOMALY"
                if prediction == -1
                else "NORMAL"
            )

        # ----------------------------------------------------
        # EXPECTED TEMPERATURE
        # ----------------------------------------------------

        expected = get_expected_weather(
            district,
            timestamp
        )

        expected_temperature = (
            expected["T2M"]
            if expected
            else current["T2M"]
        )

        # ----------------------------------------------------
        # TEMPORAL FAULT DETECTION
        # ----------------------------------------------------

        spike = detect_spike(
            current,
            previous,
            expected_temperature
        )

        stuck = detect_stuck(
            station_history[district]
        )

        drift = detect_drift(
            station_history[district],
            expected_temperature
        )

        # ----------------------------------------------------
        # FINAL FAULT TYPE
        # ----------------------------------------------------

        if spike:

            fault_type = "SPIKE"

        elif stuck:

            fault_type = "STUCK"

        elif drift:

            fault_type = "DRIFT"

        else:

            fault_type = "NONE"

        # ----------------------------------------------------
        # FINAL STATUS
        # ----------------------------------------------------

        if (
            ml_status == "ANOMALY"
            or fault_type != "NONE"
        ):

            final_status = "ANOMALY"

        else:

            final_status = "NORMAL"

        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        result = {
            "datetime": timestamp,
            "district": district,
            "T2M": current["T2M"],
            "PS": current["PS"],
            "RH2M": current["RH2M"],
            "expected_temperature": round(
                expected_temperature,
                2
            ),
            "isolation_forest_status": ml_status,
            "final_status": final_status,
            "fault_type": fault_type,
            "anomaly_score": round(
                anomaly_score,
                4
            ),
        }

        result_rows.append(result)

        print(
            f"{district:<15}"
            f"| T={current['T2M']:>6.2f}°C "
            f"| RH={current['RH2M']:>6.2f}% "
            f"| PS={current['PS']:>7.2f} hPa "
            f"| ML={ml_status:<7}"
            f"| Final={final_status:<7}"
            f"| Fault={fault_type:<5}"
        )

    # --------------------------------------------------------
    # SAVE AFTER EVERY READING
    # --------------------------------------------------------

    output_df = pd.DataFrame(
        result_rows
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved {len(output_df)} readings "
        f"to {OUTPUT_FILE}"
    )

    # Wait before next simulated hour
    if reading_index < TOTAL_READINGS - 1:

        time.sleep(
            SECONDS_PER_READING
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

output_df = pd.DataFrame(
    result_rows
)

print("\n")
print("=" * 70)
print("SIMULATION COMPLETE")
print("=" * 70)

print(
    "\nTotal readings:",
    len(output_df)
)

print("\nReadings per district:")

print(
    output_df["district"]
    .value_counts()
    .sort_index()
)

print("\nFinal status:")

print(
    output_df["final_status"]
    .value_counts()
)

print("\nFault types:")

print(
    output_df["fault_type"]
    .value_counts()
)

print("\nAnomalies by district:")

print(
    output_df[
        output_df["final_status"]
        == "ANOMALY"
    ]
    ["district"]
    .value_counts()
    .sort_index()
)

print("\nSaved final output:")

print(OUTPUT_FILE)

print("\n" + "=" * 70)