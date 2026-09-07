from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "simulated_weather_results.csv"
)


def load_data():
    if not os.path.exists(DATA_FILE):
        return None

    df = pd.read_csv(DATA_FILE)
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


def get_health_status(row):
    """
    Convert the ML/fault detection result into
    a dashboard station health status.

    GREEN  -> Normal
    YELLOW -> Warning
    RED    -> Anomaly
    """

    # Confirmed anomaly or detected sensor fault
    if row["final_status"] == "ANOMALY":
        return "ANOMALY"

    # Borderline Isolation Forest score
    # Close to zero means the reading is getting
    # closer to the anomaly boundary.
    if row["anomaly_score"] <= 0.02:
        return "WARNING"

    return "NORMAL"


@app.route("/")
def home():
    return jsonify({
        "message": "WeatherGuard AI Backend is running",
        "status": "success"
    })


@app.route("/api/weather")
def get_weather():

    df = load_data()

    if df is None:
        return jsonify({
            "error": "Simulation data not found. Run Simulate.py first."
        }), 404

    data = df.copy()

    data["health_status"] = data.apply(
        get_health_status,
        axis=1
    )

    data["datetime"] = data["datetime"].astype(str)

    return jsonify(
        data.to_dict(orient="records")
    )


@app.route("/api/latest")
def get_latest():

    df = load_data()

    if df is None:
        return jsonify({
            "error": "Simulation data not found."
        }), 404

    latest = df.iloc[-1].copy()

    health_status = get_health_status(latest)

    latest["health_status"] = health_status

    latest["datetime"] = str(
        latest["datetime"]
    )

    return jsonify(
        latest.to_dict()
    )


@app.route("/api/summary")
def get_summary():

    df = load_data()

    if df is None:
        return jsonify({
            "error": "Simulation data not found."
        }), 404

    # Calculate health status for every reading
    df["health_status"] = df.apply(
        get_health_status,
        axis=1
    )

    total = len(df)

    normal = int(
        (df["health_status"] == "NORMAL").sum()
    )

    warnings = int(
        (df["health_status"] == "WARNING").sum()
    )

    anomalies = int(
        (df["health_status"] == "ANOMALY").sum()
    )

    spikes = int(
        (df["fault_type"] == "SPIKE").sum()
    )

    stuck = int(
        (df["fault_type"] == "STUCK").sum()
    )

    drift = int(
        (df["fault_type"] == "DRIFT").sum()
    )

    return jsonify({
        "total_readings": total,
        "normal": normal,
        "warnings": warnings,
        "anomalies": anomalies,
        "spikes": spikes,
        "stuck": stuck,
        "drift": drift
    })


@app.route("/api/alerts")
def get_alerts():

    df = load_data()

    if df is None:
        return jsonify({
            "error": "Simulation data not found."
        }), 404

    alerts = df[
        df["final_status"] == "ANOMALY"
    ].copy()

    alerts["health_status"] = alerts.apply(
        get_health_status,
        axis=1
    )

    alerts["datetime"] = alerts[
        "datetime"
    ].astype(str)

    return jsonify(
        alerts.to_dict(orient="records")
    )


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )