import os
import time
import joblib
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SECONDS_PER_READING = 15      # real seconds per simulated hour
TOTAL_READINGS = 24

# Project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILE = os.path.join(
    BASE_DIR,
    "isolation_forest_multidistrict.pkl"
)

CLEAN_DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "multidistrict_clean.csv"
)

CLIMATOLOGY_FILE = os.path.join(
    BASE_DIR,
    "data",
    "multidistrict_climatology.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "multistation_simulated_results.csv"
)

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
# DEMO FAULT SCHEDULE
# ============================================================
#
# Each entry: (fault type, first reading, last reading)
# Reading numbers are 0-based: 0 = first cycle, 23 = last cycle.
#
#   SPIKE : one sudden bad value (+22 C). Shows for ONE cycle.
#   STUCK : sensor freezes at one value. Flagged from the 3rd
#           identical reading and stays flagged while frozen.
#   DRIFT : temperature climbs +3 C more every reading. Flagged
#           from the 3rd rising reading and stays flagged.
#
# Mahbubnagar has no faults so it stays healthy for contrast.
#
# Timeline:
#   0-1   everything normal (baseline)
#   2     Hyderabad SPIKE
#   3-4   Nizamabad freezing ... flagged STUCK from 5
#   5     Sangareddy SPIKE
#   6-7   Khammam drifting ... flagged DRIFT from 8
#   7     Medak SPIKE
#   9     Hyderabad SPIKE
#   12    Sangareddy SPIKE
#   14    Medak SPIKE
#   14-15 Hanamkonda freezing ... flagged STUCK from 16
#   15-17 Karimnagar drifting ... flagged DRIFT from 17
#   16    Hyderabad SPIKE
#   19    Sangareddy SPIKE
# ============================================================

FAULT_PLAN = {
    "Hyderabad": [
        ("SPIKE", 2, 2),
        ("SPIKE", 9, 9),
        ("SPIKE", 16, 16),
    ],
    "Medak": [
        ("SPIKE", 7, 7),
        ("SPIKE", 14, 14),
    ],
    "Sangareddy": [
        ("SPIKE", 5, 5),
        ("SPIKE", 12, 12),
        ("SPIKE", 19, 19),
    ],
    "Nizamabad": [
        ("STUCK", 3, 9),
    ],
    "Hanamkonda": [
        ("STUCK", 14, 21),
    ],
    "Khammam": [
        ("DRIFT", 6, 12),
    ],
    "Karimnagar": [
        ("DRIFT", 15, 21),
    ],
}

SPIKE_SIZE = 22.0
DRIFT_STEP = 3.0


# ============================================================
# GLOBAL DATA USED BY HELPER FUNCTIONS
# ============================================================

model = None
historical = None
climatology = None


# ============================================================
# HELPER: GET EXPECTED WEATHER
# ============================================================

def get_expected_weather(district, timestamp):

    row = climatology[
        (climatology["district"].str.lower() == district.lower())
        & (climatology["month"] == timestamp.month)
        & (climatology["hour"] == timestamp.hour)
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

    # Small noise so faults stand out clearly
    temperature = (
        expected["T2M"]
        + np.random.normal(0, 0.5)
    )

    humidity = (
        expected["RH2M"]
        + np.random.normal(0, 2.0)
    )

    pressure = (
        expected["PS"]
        + np.random.normal(0, 0.8)
    )

    humidity = np.clip(
        humidity,
        5,
        100
    )

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
    previous_reading,
    stuck_values
):

    for fault, start, end in FAULT_PLAN.get(
        district,
        []
    ):

        if not (
            start
            <= reading_index
            <= end
        ):
            continue

        if fault == "SPIKE":

            reading["T2M"] = round(
                reading["T2M"] + SPIKE_SIZE,
                2
            )

        elif fault == "STUCK":

            # Freeze at the last healthy reading
            # before the fault began
            if district not in stuck_values:

                if previous_reading is not None:

                    stuck_values[district] = (
                        previous_reading["T2M"]
                    )

                else:

                    stuck_values[district] = (
                        reading["T2M"]
                    )

            reading["T2M"] = (
                stuck_values[district]
            )

        elif fault == "DRIFT":

            reading["T2M"] = round(
                reading["T2M"]
                + (
                    reading_index
                    - start
                    + 1
                ) * DRIFT_STEP,
                2,
            )

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

    return (
        temperature_change >= 10
        and deviation >= 8
    )


def detect_stuck(history):

    if len(history) < 3:
        return False

    recent = [
        row["T2M"]
        for row in history[-3:]
    ]

    return (
        max(recent)
        - min(recent)
    ) < 0.01


def detect_drift(
    history,
    expected_temperature
):

    if len(history) < 3:
        return False

    recent = [
        row["T2M"]
        for row in history[-3:]
    ]

    increasing = (
        recent[0]
        < recent[1]
        < recent[2]
    )

    decreasing = (
        recent[0]
        > recent[1]
        > recent[2]
    )

    deviation = abs(
        recent[-1]
        - expected_temperature
    )

    return (
        (increasing or decreasing)
        and deviation >= 5
    )


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
        ignore_index=True,
    )

    combined["datetime"] = pd.to_datetime(
        combined["datetime"]
    )

    combined = (
        combined
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    combined["T2M_diff"] = (
        combined["T2M"].diff()
    )

    combined["PS_diff"] = (
        combined["PS"].diff()
    )

    combined["RH2M_diff"] = (
        combined["RH2M"].diff()
    )

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

    combined = combined.merge(
        climatology,
        on=[
            "district",
            "month",
            "hour"
        ],
        how="left",
    )

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
# MAIN SIMULATION FUNCTION
# ============================================================

def run_simulation():

    global model
    global historical
    global climatology

    # Same random numbers every run
    # -> repeatable demo for the jury
    np.random.seed(42)

    # --------------------------------------------------------
    # LOAD MODEL AND DATA
    # --------------------------------------------------------

    print("=" * 70)
    print(
        "WEATHERGUARD AI - "
        "MULTI-STATION LIVE SIMULATOR"
    )
    print("=" * 70)

    print("\nLoading model...")

    model = joblib.load(
        MODEL_FILE
    )

    print(
        "Model loaded successfully."
    )

    print(
        "\nLoading historical weather data..."
    )

    historical = pd.read_csv(
        CLEAN_DATA_FILE
    )

    historical["datetime"] = pd.to_datetime(
        historical["datetime"]
    )

    print(
        "Historical rows:",
        len(historical)
    )

    print(
        "\nLoading climatology..."
    )

    climatology = pd.read_csv(
        CLIMATOLOGY_FILE
    )

    print(
        "Climatology loaded successfully."
    )

    # --------------------------------------------------------
    # PREPARE SIMULATION
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    if os.path.exists(
        OUTPUT_FILE
    ):

        try:
            os.remove(
                OUTPUT_FILE
            )

        except PermissionError:

            print(
                "\nWARNING: Previous output "
                "CSV is currently locked."
            )

            print(
                "Please close any program "
                "using the CSV and try again."
            )

            return

    print(
        "\nPrevious simulation file removed."
    )

    # One shared start time so all 8 stations
    # always have the SAME timestamp
    START_TIME = (
        historical["datetime"].max()
    )

    station_history = {
        district: []
        for district in DISTRICTS
    }

    # Remembers frozen value of stuck sensor
    stuck_values = {}

    print(
        "\nFault plan "
        "(reading numbers shown 1-based, like the log):"
    )

    for district in DISTRICTS:

        events = FAULT_PLAN.get(
            district,
            []
        )

        if events:

            text = ", ".join(
                (
                    f"{fault}@{start + 1}"
                    if start == end
                    else
                    f"{fault}@{start + 1}-{end + 1}"
                )
                for fault, start, end in events
            )

        else:

            text = "NONE (healthy)"

        print(
            f"  {district:<15} -> {text}"
        )

    # --------------------------------------------------------
    # LIVE SIMULATION
    # --------------------------------------------------------

    result_rows = []

    print("\n")
    print("=" * 70)
    print("STARTING LIVE SIMULATION")
    print("=" * 70)

    for reading_index in range(
        TOTAL_READINGS
    ):

        print(
            f"\nREADING "
            f"{reading_index + 1}"
            f"/{TOTAL_READINGS}"
        )

        # Same timestamp for every station
        # in this cycle
        timestamp = (
            START_TIME
            + pd.Timedelta(
                hours=reading_index + 1
            )
        )

        for district in DISTRICTS:

            weather = generate_normal_weather(
                district,
                timestamp
            )

            if weather is None:

                print(
                    f"{district:<15}"
                    "| no climatology for this "
                    "month/hour, skipped"
                )

                continue

            previous = None

            if station_history[
                district
            ]:

                previous = (
                    station_history[
                        district
                    ][-1]
                )

            weather = apply_fault(
                district,
                reading_index,
                weather,
                previous,
                stuck_values
            )

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

            station_history[
                district
            ].append(
                current
            )

            # ------------------------------------------------
            # ML FEATURES
            # ------------------------------------------------

            feature_data = (
                create_features_for_station(
                    district,
                    station_history[
                        district
                    ]
                )
            )

            X = pd.DataFrame(
                [
                    feature_data.iloc[-1][
                        FEATURES
                    ]
                ]
            )

            X = X.replace(
                [
                    np.inf,
                    -np.inf
                ],
                np.nan
            )

            if X.isna().any().any():

                ml_status = "NORMAL"
                anomaly_score = 0.0

            else:

                prediction = (
                    model.predict(X)[0]
                )

                anomaly_score = float(
                    model.decision_function(X)[0]
                )

                ml_status = (
                    "ANOMALY"
                    if prediction == -1
                    else "NORMAL"
                )

            # ------------------------------------------------
            # EXPECTED TEMPERATURE
            # ------------------------------------------------

            expected = (
                get_expected_weather(
                    district,
                    timestamp
                )
            )

            expected_temperature = (
                expected["T2M"]
                if expected
                else current["T2M"]
            )

            # ------------------------------------------------
            # RULE-BASED FAULTS
            # ------------------------------------------------

            spike = detect_spike(
                current,
                previous,
                expected_temperature
            )

            stuck = detect_stuck(
                station_history[
                    district
                ]
            )

            drift = detect_drift(
                station_history[
                    district
                ],
                expected_temperature
            )

            if spike:

                fault_type = "SPIKE"

            elif stuck:

                fault_type = "STUCK"

            elif drift:

                fault_type = "DRIFT"

            elif ml_status == "ANOMALY":

                fault_type = "UNCLASSIFIED"

            else:

                fault_type = "NONE"

            # ------------------------------------------------
            # FINAL STATUS
            # ------------------------------------------------

            if (
                ml_status == "ANOMALY"
                or fault_type != "NONE"
            ):

                final_status = "ANOMALY"

            else:

                final_status = "NORMAL"

            # ------------------------------------------------
            # SAVE RESULT IN MEMORY
            # ------------------------------------------------

            result_rows.append({

                "datetime": timestamp,

                "district": district,

                "T2M": current["T2M"],

                "PS": current["PS"],

                "RH2M": current["RH2M"],

                "expected_temperature":
                    round(
                        expected_temperature,
                        2
                    ),

                "isolation_forest_status":
                    ml_status,

                "final_status":
                    final_status,

                "fault_type":
                    fault_type,

                "anomaly_score":
                    round(
                        anomaly_score,
                        4
                    ),
            })

            print(
                f"{district:<15}"
                f"| T={current['T2M']:>6.2f}°C "
                f"| RH={current['RH2M']:>6.2f}% "
                f"| PS={current['PS']:>7.2f} hPa "
                f"| ML={ml_status:<7}"
                f"| Final={final_status:<7}"
                f"| Fault={fault_type:<12}"
            )

        # ----------------------------------------------------
        # SAVE AFTER EVERY READING
        # WINDOWS-SAFE ATOMIC WRITE
        # ----------------------------------------------------

        output_df = pd.DataFrame(
            result_rows
        )

        tmp_file = (
            OUTPUT_FILE
            + ".tmp"
        )

        try:

            output_df.to_csv(
                tmp_file,
                index=False
            )

            os.replace(
                tmp_file,
                OUTPUT_FILE
            )

        except PermissionError:

            print(
                "WARNING: Could not replace "
                "output CSV this cycle. Retrying..."
            )

            time.sleep(0.5)

            try:

                os.replace(
                    tmp_file,
                    OUTPUT_FILE
                )

            except PermissionError:

                print(
                    "WARNING: CSV still locked. "
                    "Skipping this save cycle."
                )

                # Clean up temporary file if it still exists
                if os.path.exists(
                    tmp_file
                ):

                    try:
                        os.remove(
                            tmp_file
                        )
                    except PermissionError:
                        pass

        print(
            f"\nSaved {len(output_df)} readings "
            f"to {OUTPUT_FILE}"
        )

        if (
            reading_index
            < TOTAL_READINGS - 1
        ):

            time.sleep(
                SECONDS_PER_READING
            )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

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

    print(
        "\nReadings per district:"
    )

    print(
        output_df[
            "district"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        "\nFinal status:"
    )

    print(
        output_df[
            "final_status"
        ]
        .value_counts()
    )

    print(
        "\nFault types:"
    )

    print(
        output_df[
            "fault_type"
        ]
        .value_counts()
    )

    print(
        "\nAnomalies by district:"
    )

    print(
        output_df[
            output_df[
                "final_status"
            ] == "ANOMALY"
        ][
            "district"
        ]
        .value_counts()
        .sort_index()
    )

    print(
        "\nSaved final output:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 70
    )


# ============================================================
# ALLOW NORMAL TERMINAL EXECUTION TOO
# ============================================================

if __name__ == "__main__":
    run_simulation()