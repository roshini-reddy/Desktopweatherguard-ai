import pandas as pd
import numpy as np
import joblib
import time
import os

# ============================================================
# WEATHERGUARD AI - LIVE AWS SIMULATOR
# ============================================================

MODEL_FILE = "isolation_forest_hyderabad.pkl"

CLEAN_FILE = "data/hyderabad_clean.csv"

CLIMATOLOGY_FILE = "data/hyderabad_climatology.csv"

OUTPUT_FILE = "data/simulated_weather_results.csv"

# ------------------------------------------------------------
# Simulation speed
# 5 real seconds = 1 simulated hour
# ------------------------------------------------------------

SECONDS_PER_READING = 5


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading Isolation Forest model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

print("Loading historical weather data...")

historical = pd.read_csv(CLEAN_FILE)

historical["datetime"] = pd.to_datetime(
    historical["datetime"]
)

historical = historical.sort_values(
    "datetime"
).reset_index(drop=True)

print(
    f"Historical rows loaded: {len(historical)}"
)


# ============================================================
# LOAD CLIMATOLOGY
# ============================================================

print("Loading climatology...")

climatology = pd.read_csv(
    CLIMATOLOGY_FILE
)

print("Climatology loaded.")


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURE_COLS = [
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
# FAULT DETECTION
# ============================================================

def detect_spike(
    current_row,
    previous_row,
    expected_temperature
):

    if previous_row is None:
        return False

    temperature_change = abs(
        current_row["T2M"]
        -
        previous_row["T2M"]
    )

    deviation = abs(
        current_row["T2M"]
        -
        expected_temperature
    )

    if (
        temperature_change >= 10
        and deviation >= 8
    ):
        return True

    return False


def detect_stuck(
    recent_temperatures
):

    if len(recent_temperatures) < 4:
        return False

    last_four = recent_temperatures[-4:]

    temperature_range = (
        max(last_four)
        -
        min(last_four)
    )

    if temperature_range < 0.01:
        return True

    return False


def detect_drift(
    recent_temperatures,
    current_temperature,
    expected_temperature
):

    if len(recent_temperatures) < 4:
        return False

    last_four = recent_temperatures[-4:]

    increasing = (
        last_four[0]
        <
        last_four[1]
        <
        last_four[2]
        <
        last_four[3]
    )

    decreasing = (
        last_four[0]
        >
        last_four[1]
        >
        last_four[2]
        >
        last_four[3]
    )

    deviation = abs(
        current_temperature
        -
        expected_temperature
    )

    if (
        (increasing or decreasing)
        and deviation >= 5
    ):
        return True

    return False


# ============================================================
# GET CLIMATOLOGY VALUES
# ============================================================

def get_expected_values(
    month,
    hour
):

    match = climatology[
        (climatology["month"] == month)
        &
        (climatology["hour"] == hour)
    ]

    if len(match) == 0:

        # Fallback to overall means
        return (
            historical["T2M"].mean(),
            historical["PS"].mean(),
            historical["RH2M"].mean(),
            historical["T2M"].std(),
            historical["PS"].std(),
            historical["RH2M"].std(),
        )

    row = match.iloc[0]

    return (
        row["T2M_mean"],
        row["PS_mean"],
        row["RH2M_mean"],
        row["T2M_std"],
        row["PS_std"],
        row["RH2M_std"],
    )


# ============================================================
# CREATE OUTPUT FILE
# ============================================================

if os.path.exists(OUTPUT_FILE):

    os.remove(OUTPUT_FILE)

print()
print("Previous simulation results cleared.")

print()
print("Starting live AWS simulation...")
print(
    f"New reading every {SECONDS_PER_READING} seconds."
)

print()


# ============================================================
# SIMULATION START TIME
# ============================================================

last_historical_time = historical[
    "datetime"
].max()

simulation_start = (
    last_historical_time
    +
    pd.Timedelta(hours=1)
)


# ============================================================
# STORAGE
# ============================================================

simulated_rows = []

result_rows = []

recent_temperatures = []


# ============================================================
# RUN LIVE SIMULATION
# ============================================================

for i in range(24):

    # --------------------------------------------------------
    # Simulated timestamp
    # --------------------------------------------------------

    current_time = (
        simulation_start
        +
        pd.Timedelta(hours=i)
    )

    month = current_time.month

    hour = current_time.hour


    # --------------------------------------------------------
    # Expected weather from historical climatology
    # --------------------------------------------------------

    (
        expected_temperature,
        expected_pressure,
        expected_humidity,
        temperature_std,
        pressure_std,
        humidity_std
    ) = get_expected_values(
        month,
        hour
    )


    # --------------------------------------------------------
    # Generate normal sensor values
    # --------------------------------------------------------

    temperature = (
        expected_temperature
        +
        np.random.normal(
            0,
            max(temperature_std * 0.15, 0.3)
        )
    )

    pressure = (
        expected_pressure
        +
        np.random.normal(
            0,
            max(pressure_std * 0.15, 0.1)
        )
    )

    humidity = (
        expected_humidity
        +
        np.random.normal(
            0,
            max(humidity_std * 0.15, 0.5)
        )
    )


    # --------------------------------------------------------
    # Keep values realistic
    # --------------------------------------------------------

    humidity = np.clip(
        humidity,
        5,
        100
    )


    # ========================================================
    # FAULT INJECTION
    # ========================================================

    # --------------------------------------------------------
    # SPIKE
    # --------------------------------------------------------

    if i == 5:

        temperature += 25

        print(
            "⚡ Injecting SPIKE fault..."
        )


    # --------------------------------------------------------
    # STUCK SENSOR
    # --------------------------------------------------------

    if 10 <= i <= 14:

        if i == 10:

            stuck_temperature = temperature

        temperature = stuck_temperature

        if i == 10:

            print(
                "⏸ Injecting STUCK fault..."
            )


    # --------------------------------------------------------
    # DRIFT
    # --------------------------------------------------------

    if i >= 17:

        drift_amount = (
            i - 16
        ) * 2

        temperature += drift_amount

        if i == 17:

            print(
                "📈 Injecting DRIFT fault..."
            )


    # ========================================================
    # CREATE CURRENT ROW
    # ========================================================

    current_row = {
        "datetime": current_time,
        "T2M": temperature,
        "PS": pressure,
        "RH2M": humidity,
    }


    simulated_rows.append(
        current_row
    )


    # ========================================================
    # COMBINE HISTORICAL + SIMULATED
    # ========================================================

    temp_simulated_df = pd.DataFrame(
        simulated_rows
    )

    combined = pd.concat(
        [
            historical[
                [
                    "datetime",
                    "T2M",
                    "PS",
                    "RH2M"
                ]
            ],
            temp_simulated_df
        ],
        ignore_index=True
    )


    combined = combined.sort_values(
        "datetime"
    ).reset_index(drop=True)


    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

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


    combined["hour"] = (
        combined["datetime"].dt.hour
    )

    combined["month"] = (
        combined["datetime"].dt.month
    )


    # ========================================================
    # MERGE CLIMATOLOGY
    # ========================================================

    combined = combined.merge(
        climatology,
        on=[
            "month",
            "hour"
        ],
        how="left"
    )


    # ========================================================
    # SEASONAL Z-SCORES
    # ========================================================

    combined[
        "T2M_seasonal_zscore"
    ] = (
        combined["T2M"]
        -
        combined["T2M_mean"]
    ) / combined["T2M_std"]

    combined[
        "PS_seasonal_zscore"
    ] = (
        combined["PS"]
        -
        combined["PS_mean"]
    ) / combined["PS_std"]

    combined[
        "RH2M_seasonal_zscore"
    ] = (
        combined["RH2M"]
        -
        combined["RH2M_mean"]
    ) / combined["RH2M_std"]


    # ========================================================
    # CURRENT SIMULATED ROW
    # ========================================================

    row = combined.iloc[-1].copy()


    # ========================================================
    # MODEL PREDICTION
    # ========================================================

    X = pd.DataFrame(
        [
            row[FEATURE_COLS]
        ]
    )


    # Replace any unexpected NaN values
    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    X = X.fillna(0)


    prediction = model.predict(X)[0]

    anomaly_score = (
        model.decision_function(X)[0]
    )


    if prediction == -1:

        isolation_forest_status = (
            "ANOMALY"
        )

    else:

        isolation_forest_status = (
            "NORMAL"
        )


    # ========================================================
    # FAULT DETECTION
    # ========================================================

    previous_row = None

    if len(simulated_rows) >= 2:

        previous_row = simulated_rows[-2]


    recent_temperatures.append(
        temperature
    )


    spike_detected = detect_spike(
        current_row,
        previous_row,
        expected_temperature
    )


    stuck_detected = detect_stuck(
        recent_temperatures
    )


    drift_detected = detect_drift(
        recent_temperatures,
        temperature,
        expected_temperature
    )


    # ========================================================
    # DETERMINE FAULT TYPE
    # ========================================================

    if spike_detected:

        fault_type = "SPIKE"

    elif stuck_detected:

        fault_type = "STUCK"

    elif drift_detected:

        fault_type = "DRIFT"

    else:

        fault_type = "NONE"


    # ========================================================
    # FINAL STATUS
    # ========================================================

    if (
        isolation_forest_status == "ANOMALY"
        or fault_type != "NONE"
    ):

        final_status = "ANOMALY"

    else:

        final_status = "NORMAL"


    # ========================================================
    # SAVE RESULT
    # ========================================================

    result = {

        "datetime": current_time,

        "T2M": temperature,

        "PS": pressure,

        "RH2M": humidity,

        "isolation_forest_status":
            isolation_forest_status,

        "final_status":
            final_status,

        "fault_type":
            fault_type,

        "anomaly_score":
            anomaly_score,

        "expected_temperature":
            expected_temperature,
    }


    result_rows.append(
        result
    )


    # ========================================================
    # WRITE TO CSV IMMEDIATELY
    # ========================================================

    results_df = pd.DataFrame(
        result_rows
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    print(
        f"{current_time} | "
        f"T={temperature:.2f}°C | "
        f"RH={humidity:.2f}% | "
        f"PS={pressure:.2f} hPa | "
        f"ML={isolation_forest_status} | "
        f"Final={final_status} | "
        f"Fault={fault_type} | "
        f"Score={anomaly_score:.4f}"
    )


    # ========================================================
    # WAIT BEFORE NEXT READING
    # ========================================================

    if i < 23:

        time.sleep(
            SECONDS_PER_READING
        )


# ============================================================
# SIMULATION FINISHED
# ============================================================

print()
print("=" * 60)
print("LIVE SIMULATION COMPLETED")
print("=" * 60)

print()

print(
    "Final status counts:"
)

print(
    pd.Series(
        [
            r["final_status"]
            for r in result_rows
        ]
    ).value_counts()
)

print()

print(
    "Detected fault types:"
)

print(
    pd.Series(
        [
            r["fault_type"]
            for r in result_rows
        ]
    ).value_counts()
)

print()

print(
    f"Saved: {OUTPUT_FILE}"
)