from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = "../data/multistation_simulated_results.csv"

# -------------------------------------------------------
# Telangana district coordinates
# -------------------------------------------------------

STATION_COORDINATES = {
    "Hyderabad":    {"lat": 17.3850, "lon": 78.4867},
    "Medak":        {"lat": 18.0453, "lon": 78.2608},
    "Sangareddy":   {"lat": 17.6199, "lon": 78.0820},
    "Hanamkonda":   {"lat": 18.0000, "lon": 79.5800},
    "Nizamabad":    {"lat": 18.6725, "lon": 78.0941},
    "Karimnagar":   {"lat": 18.4386, "lon": 79.1288},
    "Khammam":      {"lat": 17.2473, "lon": 80.1514},
    "Mahbubnagar":  {"lat": 16.7488, "lon": 78.0035},
}


# -------------------------------------------------------
# Load simulation CSV
# -------------------------------------------------------

def load_data():

    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()

    df = pd.read_csv(DATA_FILE)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


# -------------------------------------------------------
# API 1 : Latest reading of all stations
# -------------------------------------------------------

@app.route("/api/stations")
def get_all_stations():

    df = load_data()

    if df.empty:
        return jsonify([])

    latest = (
        df.sort_values("datetime")
          .groupby("district")
          .tail(1)
    )

    stations = []

    for _, row in latest.iterrows():

        stations.append({

            "district": row["district"],

            "lat": STATION_COORDINATES[row["district"]]["lat"],
            "lon": STATION_COORDINATES[row["district"]]["lon"],

            "temperature": round(float(row["T2M"]), 2),
            "humidity": round(float(row["RH2M"]), 2),
            "pressure": round(float(row["PS"]), 2),

            "expected_temperature": round(
                float(row["expected_temperature"]), 2
            ),

            "status": row["final_status"],
            "fault": row["fault_type"],

            "score": round(float(row["anomaly_score"]), 4),

            "time": row["datetime"].strftime("%Y-%m-%d %H:%M")
        })

    return jsonify(stations)


# -------------------------------------------------------
# API 2 : History of one district
# -------------------------------------------------------

@app.route("/api/history/<district>")
def history(district):

    df = load_data()

    if df.empty:
        return jsonify([])

    history_df = (
        df[df["district"].str.lower() == district.lower()]
        .sort_values("datetime")
    )

    result = []

    for _, row in history_df.iterrows():

        result.append({

            "time": row["datetime"].strftime("%H:%M"),

            "temperature": round(float(row["T2M"]), 2),
            "humidity": round(float(row["RH2M"]), 2),
            "pressure": round(float(row["PS"]), 2),

            "status": row["final_status"]
        })

    return jsonify(result)


# -------------------------------------------------------
# API 3 : Active alerts only
# -------------------------------------------------------

@app.route("/api/alerts")
def alerts():

    df = load_data()

    if df.empty:
        return jsonify([])

    latest = (
        df.sort_values("datetime")
          .groupby("district")
          .tail(1)
    )

    active = latest[latest["final_status"] == "ANOMALY"]

    result = []

    for _, row in active.iterrows():

        result.append({

            "district": row["district"],

            "fault": row["fault_type"],

            "temperature": round(float(row["T2M"]), 2),

            "time": row["datetime"].strftime("%H:%M")
        })

    return jsonify(result)


# -------------------------------------------------------
# API 4 : Dashboard summary
# -------------------------------------------------------

@app.route("/api/summary")
def summary():

    df = load_data()

    if df.empty:
        return jsonify({})

    latest = (
        df.sort_values("datetime")
          .groupby("district")
          .tail(1)
    )

    total = len(latest)

    healthy = len(
        latest[latest["final_status"] == "NORMAL"]
    )

    anomaly = total - healthy

    return jsonify({

        "totalStations": total,
        "healthyStations": healthy,
        "anomalyStations": anomaly,

        "spike": len(latest[latest["fault_type"] == "SPIKE"]),
        "stuck": len(latest[latest["fault_type"] == "STUCK"]),
        "drift": len(latest[latest["fault_type"] == "DRIFT"]),
    })


# -------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)