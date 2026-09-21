from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import threading

# =========================================================
# IMPORT SIMULATION FUNCTION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..")
)

import sys

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Simulate_MultiStation import run_simulation


app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(
    BASE_DIR, "..", "data", "multistation_simulated_results.csv"
)

STATION_COORDINATES = {
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Medak": {"lat": 18.0453, "lon": 78.2608},
    "Sangareddy": {"lat": 17.6199, "lon": 78.0820},
    "Hanamkonda": {"lat": 18.0000, "lon": 79.5800},
    "Nizamabad": {"lat": 18.6725, "lon": 78.0941},
    "Karimnagar": {"lat": 18.4386, "lon": 79.1288},
    "Khammam": {"lat": 17.2473, "lon": 80.1514},
    "Mahbubnagar": {"lat": 16.7488, "lon": 78.0035},
}


# =========================================================
# SIMULATION STATE
# =========================================================
#
# These variables allow the React dashboard to know whether
# the simulation is currently running.
# =========================================================

simulation_running = False
simulation_lock = threading.Lock()


def simulation_worker():
    global simulation_running

    try:
        print("\n" + "=" * 70)
        print("BACKGROUND SIMULATION STARTED")
        print("=" * 70)

        run_simulation()

        print("\n" + "=" * 70)
        print("BACKGROUND SIMULATION FINISHED")
        print("=" * 70)

    except Exception as e:
        print("\nSIMULATION ERROR:", e)

    finally:
        simulation_running = False


# =========================================================
# START SIMULATION
# =========================================================

@app.route("/api/simulation/start", methods=["POST"])
def start_simulation():

    global simulation_running

    # Prevent two simulations from running at the
    # same time if the jury clicks the button twice.
    with simulation_lock:

        if simulation_running:

            return jsonify({
                "success": False,
                "running": True,
                "message": "Simulation is already running."
            }), 409

        simulation_running = True

        simulation_thread = threading.Thread(
            target=simulation_worker,
            daemon=True
        )

        simulation_thread.start()

    print("Simulation requested from dashboard.")

    return jsonify({
        "success": True,
        "running": True,
        "message": "Simulation started successfully."
    })


# =========================================================
# SIMULATION STATUS
# =========================================================

@app.route("/api/simulation/status")
def simulation_status():

    return jsonify({
        "running": simulation_running
    })


# =========================================================
# LOAD CURRENT SIMULATION DATA
# Keeps the last good read so the dashboard never flickers
# if the CSV is being rewritten at the moment of reading.
# =========================================================

_last_good_df = pd.DataFrame()


def load_data():
    global _last_good_df

    if not os.path.exists(DATA_FILE):
        return _last_good_df

    try:
        df = pd.read_csv(DATA_FILE)

        if df.empty or "datetime" not in df.columns:
            return _last_good_df

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["datetime"]
        )

        if df.empty:
            return _last_good_df

        _last_good_df = df
        return df

    except Exception as e:
        print("DATA READ ERROR:", e)
        return _last_good_df


# =========================================================
# GET CURRENT SIMULATION CYCLE
# =========================================================

def get_current_cycle():
    df = load_data()

    if df.empty:
        return df

    # The simulator writes all 8 stations for the same timestamp.
    latest_time = df["datetime"].max()

    current = df[
        df["datetime"] == latest_time
    ].copy()

    # Keep only our 8 known stations
    current = current[
        current["district"].isin(
            STATION_COORDINATES.keys()
        )
    ]

    return current


# =========================================================
# NO-CACHE RESPONSE
# =========================================================

def no_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, "
        "max-age=0, s-maxage=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# =========================================================
# STATIONS
# =========================================================

@app.route("/api/stations")
def get_all_stations():

    current = get_current_cycle()

    if current.empty:
        return no_cache(
            jsonify([])
        )

    stations = []

    for _, row in current.iterrows():

        district = row["district"]

        if district not in STATION_COORDINATES:
            continue

        stations.append({

            "district": district,

            "lat":
                STATION_COORDINATES[
                    district
                ]["lat"],

            "lon":
                STATION_COORDINATES[
                    district
                ]["lon"],

            "temperature":
                round(
                    float(row["T2M"]),
                    2
                ),

            "humidity":
                round(
                    float(row["RH2M"]),
                    2
                ),

            "pressure":
                round(
                    float(row["PS"]),
                    2
                ),

            "expected_temperature":
                round(
                    float(
                        row[
                            "expected_temperature"
                        ]
                    ),
                    2
                ),

            "status":
                str(
                    row["final_status"]
                ),

            "fault":
                str(
                    row["fault_type"]
                ),

            "score":
                round(
                    float(
                        row["anomaly_score"]
                    ),
                    4
                ),

            "time":
                row["datetime"].strftime(
                    "%Y-%m-%d %H:%M"
                ),
        })

    print(
        "CURRENT CYCLE:",
        current["datetime"].iloc[0],
        "| ANOMALIES:",
        len(
            current[
                current["final_status"]
                == "ANOMALY"
            ]
        ),
    )

    return no_cache(
        jsonify(stations)
    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/api/history/<district>")
def history(district):

    df = load_data()

    if df.empty:
        return no_cache(
            jsonify([])
        )

    history_df = df[
        df["district"].str.lower()
        == district.lower()
    ].sort_values(
        "datetime"
    )

    result = []

    for _, row in history_df.iterrows():

        result.append({

            "time":
                row["datetime"].strftime(
                    "%H:%M"
                ),

            "temperature":
                round(
                    float(row["T2M"]),
                    2
                ),

            "humidity":
                round(
                    float(row["RH2M"]),
                    2
                ),

            "pressure":
                round(
                    float(row["PS"]),
                    2
                ),

            "status":
                str(
                    row["final_status"]
                ),
        })

    return no_cache(
        jsonify(result)
    )


# =========================================================
# ACTIVE ALERTS
# =========================================================

@app.route("/api/alerts")
def alerts():

    current = get_current_cycle()

    if current.empty:
        return no_cache(
            jsonify([])
        )

    active = current[
        current["final_status"]
        == "ANOMALY"
    ]

    result = []

    for _, row in active.iterrows():

        result.append({

            "district":
                row["district"],

            "fault":
                row["fault_type"],

            "temperature":
                round(
                    float(row["T2M"]),
                    2
                ),

            "time":
                row["datetime"].strftime(
                    "%H:%M"
                ),
        })

    return no_cache(
        jsonify(result)
    )


# =========================================================
# SUMMARY
# =========================================================

@app.route("/api/summary")
def summary():

    current = get_current_cycle()

    if current.empty:

        return no_cache(
            jsonify({
                "totalStations": 0,
                "healthyStations": 0,
                "anomalyStations": 0,
                "spike": 0,
                "stuck": 0,
                "drift": 0,
            })
        )

    result = {

        "totalStations":
            len(current),

        "healthyStations":
            len(
                current[
                    current["final_status"]
                    == "NORMAL"
                ]
            ),

        "anomalyStations":
            len(
                current[
                    current["final_status"]
                    == "ANOMALY"
                ]
            ),

        "spike":
            len(
                current[
                    current["fault_type"]
                    == "SPIKE"
                ]
            ),

        "stuck":
            len(
                current[
                    current["fault_type"]
                    == "STUCK"
                ]
            ),

        "drift":
            len(
                current[
                    current["fault_type"]
                    == "DRIFT"
                ]
            ),
    }

    print(
        "SUMMARY:",
        result
    )

    return no_cache(
        jsonify(result)
    )


# =========================================================
# DEBUG ENDPOINT
# =========================================================

@app.route("/api/debug")
def debug():

    df = load_data()

    if df.empty:

        return no_cache(
            jsonify({
                "rows": 0,
                "message":
                    "No simulation data",
            })
        )

    latest_time = df["datetime"].max()

    current = df[
        df["datetime"]
        == latest_time
    ]

    result = {

        "totalRows":
            len(df),

        "latestTime":
            str(latest_time),

        "currentCycleRows":
            len(current),

        "currentCycle":
            current[
                [
                    "district",
                    "datetime",
                    "final_status",
                    "fault_type",
                ]
            ].to_dict(
                orient="records"
            ),
    }

    return no_cache(
        jsonify(result)
    )


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    print(
        "WeatherGuard AI backend starting..."
    )

    print(
        "Reading:",
        os.path.abspath(
            DATA_FILE
        )
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )