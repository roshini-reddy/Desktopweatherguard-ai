import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import "../index.css";


const API =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:5000";


// =========================================================
// STATION DETAILS
// =========================================================

function StationDetails() {

  const {
    district,
  } = useParams();

  const navigate =
    useNavigate();


  // =======================================================
  // STATE
  // =======================================================

  const [
    station,
    setStation,
  ] = useState(null);

  const [
    history,
    setHistory,
  ] = useState([]);

  const [
    error,
    setError,
  ] = useState("");


  // =======================================================
  // FETCH STATION DATA
  // =======================================================

  const fetchStationData =
    async () => {

      try {

        const response =
          await fetch(
            `${API}/api/stations`
          );

        if (!response.ok) {
          throw new Error(
            "Unable to load station"
          );
        }

        const data =
          await response.json();

        const decodedDistrict =
          decodeURIComponent(
            district || ""
          );

        const selected =
          data.find(
            (item) =>
              item.district.toLowerCase() ===
              decodedDistrict.toLowerCase()
          );

        if (!selected) {

          setError(
            "Station not found."
          );

          return;

        }

        setStation(selected);

        setError("");

      } catch (err) {

        console.error(err);

        setError(
          "Unable to connect to WeatherGuard AI backend."
        );

      }

    };


  // =======================================================
  // FETCH HISTORY
  // =======================================================

  const fetchHistory =
    async () => {

      try {

        const decodedDistrict =
          decodeURIComponent(
            district || ""
          );

        const response =
          await fetch(
            `${API}/api/history/${encodeURIComponent(
              decodedDistrict
            )}`
          );

        if (!response.ok) {

          throw new Error(
            "History unavailable"
          );

        }

        const data =
          await response.json();

        setHistory(data);

      } catch (err) {

        console.error(
          "History error:",
          err
        );

        setHistory([]);

      }

    };


  // =======================================================
  // LIVE UPDATE
  // =======================================================

  useEffect(() => {

    fetchStationData();

    fetchHistory();


    const interval =
      setInterval(() => {

        fetchStationData();

        fetchHistory();

      }, 3000);


    return () =>
      clearInterval(interval);

  }, [district]);


  // =======================================================
  // LOGOUT
  // =======================================================

  const handleLogout =
    () => {

      localStorage.removeItem(
        "weatherguard_logged_in"
      );

      navigate("/login");

    };


  // =======================================================
  // LOADING
  // =======================================================

  if (!station && !error) {

    return (

      <div className="station-page">

        <div className="weather-motion">

          <div className="cloud cloud-one"></div>
          <div className="cloud cloud-two"></div>
          <div className="cloud cloud-three"></div>

        </div>


        <div className="station-loading">

          <div className="loading-spinner"></div>

          <h2>
            Loading station...
          </h2>

          <p>
            Connecting to WeatherGuard AI
          </p>

        </div>

      </div>

    );

  }


  // =======================================================
  // ERROR
  // =======================================================

  if (error) {

    return (

      <div className="station-page">

        <div className="station-error-card">

          <div className="error-icon">
            !
          </div>

          <h2>
            Station unavailable
          </h2>

          <p>
            {error}
          </p>

          <button
            onClick={() =>
              navigate("/dashboard")
            }
          >
            ← Back to Dashboard
          </button>

        </div>

      </div>

    );

  }


  // =======================================================
  // STATUS
  // =======================================================

  const isAnomaly =
    station.status === "ANOMALY";


  const statusText =
    isAnomaly
      ? "Anomaly Detected"
      : "Station Healthy";


  const statusClass =
    isAnomaly
      ? "status-danger"
      : "status-healthy";


  // =======================================================
  // RENDER
  // =======================================================

  return (

    <div className="station-page">


      {/* =================================================
          WEATHER BACKGROUND
      ================================================= */}

      <div className="weather-motion">

        <div className="sun-glow"></div>

        <div className="cloud cloud-one"></div>

        <div className="cloud cloud-two"></div>

        <div className="cloud cloud-three"></div>

      </div>


      {/* =================================================
          CONTENT
      ================================================= */}

      <div className="station-content">


        {/* =================================================
            TOP NAVIGATION
        ================================================= */}

        <header className="station-topbar">


          <button
            className="back-dashboard"
            onClick={() =>
              navigate("/dashboard")
            }
          >
            ← Dashboard
          </button>


          <div className="station-brand">

            <strong>
              WeatherGuard AI
            </strong>

            <span>
              Intelligent AWS Monitoring
            </span>

          </div>


          <div className="station-live">

            <span className="live-dot"></span>

            LIVE MONITORING

          </div>


          <button
            className="station-logout"
            onClick={handleLogout}
          >
            Logout
          </button>

        </header>


        {/* =================================================
            STATION HERO
        ================================================= */}

        <section className="station-hero">


          <div className="hero-left">


            <div className="station-eyebrow">

              AUTOMATIC WEATHER STATION

            </div>


            <h1>
              {station.district}
            </h1>


            <p className="station-last-reading">

              Last reading:

              <strong>
                {" "}
                {station.time}
              </strong>

            </p>


          </div>


          <div className="hero-status">


            <div
              className={`
                status-pill
                ${statusClass}
              `}
            >

              <span className="status-dot"></span>

              {statusText}

            </div>


            <div className="fault-label">

              <span>
                Fault Type
              </span>

              <strong>
                {station.fault || "NONE"}
              </strong>

            </div>

          </div>

        </section>


        {/* =================================================
            LIVE SENSOR CARDS
        ================================================= */}

        <section className="sensor-grid">


          {/* TEMPERATURE */}

          <div className="sensor-card">

            <div className="sensor-icon temperature-icon">
              🌡️
            </div>

            <div className="sensor-info">

              <span>
                Temperature
              </span>

              <strong>
                {station.temperature}°C
              </strong>

              <small>
                Expected {station.expected_temperature}°C
              </small>

            </div>

          </div>


          {/* HUMIDITY */}

          <div className="sensor-card">

            <div className="sensor-icon humidity-icon">
              💧
            </div>

            <div className="sensor-info">

              <span>
                Humidity
              </span>

              <strong>
                {station.humidity}%
              </strong>

              <small>
                Relative humidity
              </small>

            </div>

          </div>


          {/* PRESSURE */}

          <div className="sensor-card">

            <div className="sensor-icon pressure-icon">
              🌬️
            </div>

            <div className="sensor-info">

              <span>
                Atmospheric Pressure
              </span>

              <strong>
                {station.pressure}
                <small className="unit">
                  {" "}hPa
                </small>
              </strong>

              <small>
                Current pressure
              </small>

            </div>

          </div>


          {/* ANOMALY SCORE */}

          <div className="sensor-card">

            <div className="sensor-icon ai-icon">
              🤖
            </div>

            <div className="sensor-info">

              <span>
                Anomaly Score
              </span>

              <strong>
                {station.score}
              </strong>

              <small>
                Isolation Forest
              </small>

            </div>

          </div>


        </section>


        {/* =================================================
            CHARTS
        ================================================= */}

        <section className="station-charts">


          {/* =================================================
              TEMPERATURE
          ================================================= */}

          <div className="station-chart-card">


            <div className="chart-heading">

              <div>

                <span className="chart-overline">
                  SENSOR HISTORY
                </span>

                <h2>
                  Temperature Trend
                </h2>

                <p>
                  Temperature readings over time
                </p>

              </div>


              <div className="chart-unit">
                °C
              </div>

            </div>


            <div className="station-chart">

              {history.length > 0 ? (

                <LineChart
                  width={650}
                  height={300}
                  data={history}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    stroke="#d9e2ec"
                    strokeDasharray="4 4"
                  />

                  <XAxis
                    dataKey="time"
                    tick={{
                      fill: "#526173",
                      fontSize: 11,
                    }}
                    axisLine={{
                      stroke: "#cbd5e1",
                    }}
                    tickLine={false}
                  />

                  <YAxis
                    tick={{
                      fill: "#526173",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    contentStyle={{
                      background:
                        "#ffffff",
                      border:
                        "1px solid #dbe3ec",
                      borderRadius:
                        "10px",
                      color:
                        "#172033",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke="#2563eb"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{
                      r: 5,
                    }}
                  />

                </LineChart>

              ) : (

                <div className="chart-no-data">
                  No temperature history available
                </div>

              )}

            </div>

          </div>


          {/* =================================================
              HUMIDITY
          ================================================= */}

          <div className="station-chart-card">


            <div className="chart-heading">

              <div>

                <span className="chart-overline">
                  SENSOR HISTORY
                </span>

                <h2>
                  Humidity Trend
                </h2>

                <p>
                  Relative humidity readings over time
                </p>

              </div>


              <div className="chart-unit humidity-unit">
                %
              </div>

            </div>


            <div className="station-chart">

              {history.length > 0 ? (

                <LineChart
                  width={650}
                  height={300}
                  data={history}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    stroke="#d9e2ec"
                    strokeDasharray="4 4"
                  />

                  <XAxis
                    dataKey="time"
                    tick={{
                      fill: "#526173",
                      fontSize: 11,
                    }}
                    axisLine={{
                      stroke: "#cbd5e1",
                    }}
                    tickLine={false}
                  />

                  <YAxis
                    tick={{
                      fill: "#526173",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    contentStyle={{
                      background:
                        "#ffffff",
                      border:
                        "1px solid #dbe3ec",
                      borderRadius:
                        "10px",
                      color:
                        "#172033",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="humidity"
                    stroke="#0f9f8f"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{
                      r: 5,
                    }}
                  />

                </LineChart>

              ) : (

                <div className="chart-no-data">
                  No humidity history available
                </div>

              )}

            </div>

          </div>


        </section>


        {/* =================================================
            DIAGNOSIS
        ================================================= */}

        <section className="diagnosis-card">


          <div className="diagnosis-icon">

            {isAnomaly
              ? "!"
              : "✓"}

          </div>


          <div className="diagnosis-content">

            <span className="diagnosis-label">
              SENSOR DIAGNOSIS
            </span>


            <h2>

              {isAnomaly
                ? "Sensor anomaly detected"
                : "Station operating normally"}

            </h2>


            <p>

              {isAnomaly

                ? station.fault !== "NONE"

                  ? `${station.fault} fault detected at ${station.district}. The station requires attention.`

                  : "Isolation Forest detected an abnormal sensor reading."

                : "Current sensor readings are within the learned normal operating pattern."}

            </p>

          </div>


          <div className="diagnosis-meta">

            <span>
              MODEL
            </span>

            <strong>
              Isolation Forest
            </strong>

          </div>


        </section>


        {/* =================================================
            FOOTER
        ================================================= */}

        <footer className="station-footer">

          <span>
            WeatherGuard AI
          </span>

          <span>
            Real-time Automatic Weather Station Monitoring
          </span>

          <span>
            Live updates every 3 seconds
          </span>

        </footer>


      </div>

    </div>

  );

}


export default StationDetails;