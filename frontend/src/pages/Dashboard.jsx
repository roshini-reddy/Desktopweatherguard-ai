import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  MapContainer,
  TileLayer,
  Marker,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

const API =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:5000";


/* =========================================================
   LEAFLET DEFAULT ICON FIX
   ========================================================= */

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",

  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",

  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});


/* =========================================================
   CUSTOM STATION MARKER
   ========================================================= */

function createStationIcon(status) {
  let color = "#22c55e";

  if (status === "ANOMALY") {
    color = "#ef4444";
  }

  if (status === "WARNING") {
    color = "#f59e0b";
  }

  return L.divIcon({
    className: "weatherguard-marker-wrapper",

    html: `
      <div
        style="
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: ${color};
          border: 3px solid white;
          box-shadow:
            0 3px 10px rgba(0,0,0,0.28),
            0 0 0 5px ${color}33;
          cursor: pointer;
        "
      ></div>
    `,

    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}


/* =========================================================
   WEATHER ICON
   ========================================================= */

function getWeatherIcon(temperature) {
  if (temperature >= 35) {
    return "☀️";
  }

  if (temperature >= 28) {
    return "🌤️";
  }

  if (temperature >= 20) {
    return "⛅";
  }

  return "🌧️";
}


/* =========================================================
   FORMAT DATE
   ========================================================= */

function getCurrentDate() {
  return new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


/* =========================================================
   DASHBOARD
   ========================================================= */

function Dashboard() {
  const navigate = useNavigate();

  const [stations, setStations] = useState([]);
  const [summary, setSummary] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  /* =======================================================
     SIMULATION STATE
     ======================================================= */

  const [simulationRunning, setSimulationRunning] =
    useState(false);

  const [simulationMessage, setSimulationMessage] =
    useState("");


  /* =======================================================
     FETCH DASHBOARD DATA
     ======================================================= */

  const fetchDashboardData = async () => {
    try {
      const [
        stationsResponse,
        summaryResponse,
        alertsResponse,
      ] = await Promise.all([
        fetch(
          `${API}/api/stations?t=${Date.now()}`,
          {
            cache: "no-store",
          }
        ),

        fetch(
          `${API}/api/summary?t=${Date.now()}`,
          {
            cache: "no-store",
          }
        ),

        fetch(
          `${API}/api/alerts?t=${Date.now()}`,
          {
            cache: "no-store",
          }
        ),
      ]);

      if (!stationsResponse.ok) {
        throw new Error(
          "Unable to fetch station data"
        );
      }

      if (!summaryResponse.ok) {
        throw new Error(
          "Unable to fetch summary data"
        );
      }

      if (!alertsResponse.ok) {
        throw new Error(
          "Unable to fetch alerts"
        );
      }

      const stationsData =
        await stationsResponse.json();

      const summaryData =
        await summaryResponse.json();

      const alertsData =
        await alertsResponse.json();

      setStations(stationsData);
      setSummary(summaryData);
      setAlerts(alertsData);
      setError("");
      setLoading(false);

      if (stationsData.length > 0) {
        setSelectedStation((current) => {
          if (!current) {
            return stationsData[0];
          }

          const updated = stationsData.find(
            (station) =>
              station.district ===
              current.district
          );

          return (
            updated ||
            stationsData[0]
          );
        });
      }

    } catch (err) {
      console.error(
        "Dashboard error:",
        err
      );

      setError(
        "Unable to connect to WeatherGuard AI backend."
      );

      setLoading(false);
    }
  };


  /* =======================================================
     START SIMULATION
     ======================================================= */

  const startSimulation = async () => {

    if (simulationRunning) {
      return;
    }

    try {

      setSimulationMessage(
        "Starting simulation..."
      );

      const response = await fetch(
        `${API}/api/simulation/start`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          cache: "no-store",
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.message ||
          "Unable to start simulation"
        );
      }

      setSimulationRunning(true);

      setSimulationMessage(
        "Simulation running — live weather data is being generated."
      );

      // Immediately refresh dashboard
      await fetchDashboardData();

    } catch (err) {

      console.error(
        "Simulation start error:",
        err
      );

      setSimulationRunning(false);

      setSimulationMessage(
        err.message ||
        "Unable to start simulation."
      );
    }
  };


  /* =======================================================
     CHECK SIMULATION STATUS
     ======================================================= */

  const checkSimulationStatus =
    async () => {

      try {

        const response = await fetch(
          `${API}/api/simulation/status?t=${Date.now()}`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          return;
        }

        const data =
          await response.json();

        const running =
          Boolean(data.running);

        setSimulationRunning(
          running
        );

        if (running) {

          setSimulationMessage(
            "Simulation running — live weather data is being generated."
          );

        } else {

          setSimulationMessage(
            "Simulation complete."
          );
        }

      } catch (err) {

        console.error(
          "Simulation status error:",
          err
        );
      }
    };


  /* =======================================================
     LIVE UPDATE
     ======================================================= */

  useEffect(() => {

    fetchDashboardData();

    const interval =
      setInterval(
        fetchDashboardData,
        3000
      );

    return () =>
      clearInterval(interval);

  }, []);


  /* =======================================================
     SIMULATION STATUS POLLING
     ======================================================= */

  useEffect(() => {

    checkSimulationStatus();

    const interval =
      setInterval(
        checkSimulationStatus,
        3000
      );

    return () =>
      clearInterval(interval);

  }, []);


  /* =======================================================
     OPEN STATION
     ======================================================= */

  const openStation = (station) => {

    if (
      !station ||
      !station.district
    ) {
      return;
    }

    setSelectedStation(
      station
    );

    navigate(
      `/station/${encodeURIComponent(
        station.district
      )}`
    );
  };


  /* =======================================================
     LOGOUT
     ======================================================= */

  const handleLogout = () => {

    localStorage.removeItem(
      "weatherguard_logged_in"
    );

    navigate(
      "/login",
      {
        replace: true,
      }
    );
  };


  /* =======================================================
     LOADING
     ======================================================= */

  if (
    loading &&
    stations.length === 0
  ) {

    return (
      <div className="dashboard-loading">

        <div className="loading-spinner"></div>

        <h2>
          Loading WeatherGuard AI
        </h2>

        <p>
          Connecting to weather station network...
        </p>

      </div>
    );
  }


  /* =======================================================
     DASHBOARD
     ======================================================= */

  return (

    <div className="dashboard">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="top-header">

        <div className="brand-section">

          <div className="brand-weather-logo">

            <span className="brand-sun">
              ☀
            </span>

            <span className="brand-cloud">
              ☁
            </span>

          </div>

          <div>

            <h1>
              WeatherGuard AI
            </h1>

            <p>
              Intelligent Automatic Weather Station Monitoring
            </p>

          </div>

        </div>


        <div className="header-actions">

          <div className="live-block">

            <div className="live-indicator">

              <span className="live-dot"></span>

              <strong>
                LIVE MONITORING
              </strong>

            </div>

            <span className="live-date">
              {getCurrentDate()}
            </span>

          </div>


          {/* =================================================
              SIMULATE DATA BUTTON
          ================================================= */}

          <button
            className={
              simulationRunning
                ? "simulate-button simulation-running"
                : "simulate-button"
            }
            onClick={
              startSimulation
            }
            disabled={
              simulationRunning
            }
          >

            <span className="simulate-icon">
              {simulationRunning
                ? "◌"
                : "▶"}
            </span>

            {simulationRunning
              ? "Simulation Running"
              : "Simulate Data"}

          </button>
          <small className="simulation-helper-text">
  Click here to test the model
</small>


          <button
            className="logout-button"
            onClick={
              handleLogout
            }
          >

            <span className="logout-icon">
              ↪
            </span>

            Logout

          </button>

        </div>

      </header>


      {/* =================================================
          SIMULATION STATUS
      ================================================= */}

      {simulationMessage && (

        <div
          className={
            simulationRunning
              ? "simulation-status simulation-status-running"
              : "simulation-status"
          }
        >

          <span className="simulation-status-dot"></span>

          <span>
            {simulationMessage}
          </span>

        </div>

      )}


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div className="dashboard-error">

          <strong>
            Connection issue
          </strong>

          <span>
            {error}
          </span>

        </div>

      )}


      {/* =================================================
          KPI CARDS
      ================================================= */}

      <section className="kpi-grid">

        {/* TOTAL STATIONS */}

        <div className="kpi-card">

          <div className="kpi-icon blue">
            ◈
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              TOTAL STATIONS
            </span>

            <strong className="kpi-value">
              {summary.totalStations ?? 0}
            </strong>

            <span className="kpi-description">
              Monitoring network
            </span>

          </div>

        </div>


        {/* HEALTHY */}

        <div className="kpi-card">

          <div className="kpi-icon green">
            ✓
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              HEALTHY
            </span>

            <strong className="kpi-value">
              {summary.healthyStations ?? 0}
            </strong>

            <span className="kpi-description">
              Normal stations
            </span>

          </div>

        </div>


        {/* ANOMALIES */}

        <div className="kpi-card">

          <div className="kpi-icon red">
            !
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              ANOMALIES
            </span>

            <strong className="kpi-value anomaly-number">
              {summary.anomalyStations ?? 0}
            </strong>

            <span className="kpi-description">
              Stations requiring attention
            </span>

          </div>

        </div>


        {/* SPIKE */}

        <div className="kpi-card">

          <div className="kpi-icon purple">
            ↗
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              SPIKE FAULTS
            </span>

            <strong className="kpi-value">
              {summary.spike ?? 0}
            </strong>

            <span className="kpi-description">
              Sudden changes
            </span>

          </div>

        </div>


        {/* STUCK */}

        <div className="kpi-card">

          <div className="kpi-icon orange">
            ||
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              STUCK FAULTS
            </span>

            <strong className="kpi-value">
              {summary.stuck ?? 0}
            </strong>

            <span className="kpi-description">
              Repeated readings
            </span>

          </div>

        </div>


        {/* DRIFT */}

        <div className="kpi-card">

          <div className="kpi-icon pink">
            ↝
          </div>

          <div className="kpi-content">

            <span className="kpi-label">
              DRIFT FAULTS
            </span>

            <strong className="kpi-value">
              {summary.drift ?? 0}
            </strong>

            <span className="kpi-description">
              Gradual sensor drift
            </span>

          </div>

        </div>

      </section>


      {/* =================================================
          MAIN AREA
      ================================================= */}

      <section className="main-monitor-grid">


        {/* =================================================
            WEATHER STATION NETWORK
        ================================================= */}

        <div className="map-panel">

          <div className="panel-header">

            <div>

              <h2>
                Weather Station Network
              </h2>

              <p>
                Real-time station health monitoring
              </p>

            </div>

            <div className="station-count">

              <span className="station-count-icon">
                ◉
              </span>

              {stations.length} stations

            </div>

          </div>


          {/* MAP LEGEND */}

          <div className="map-legend">

            <div className="legend-item">

              <span className="legend-dot healthy"></span>

              Healthy

            </div>

            <div className="legend-item">

              <span className="legend-dot warning"></span>

              Warning

            </div>

            <div className="legend-item">

              <span className="legend-dot anomaly"></span>

              Anomaly

            </div>

          </div>


          {/* MAP */}

          <div className="map-container">

            <MapContainer
              center={[
                17.8,
                78.8
              ]}
              zoom={7.4}
              minZoom={6}
              maxZoom={12}
              scrollWheelZoom={true}
              style={{
  height: "calc(100% - 30px)",
  width: "100%",
}}
            >

              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {stations.map(
                (station) => (

                  <Marker
                    key={
                      station.district
                    }
                    position={[
                      Number(
                        station.lat
                      ),
                      Number(
                        station.lon
                      ),
                    ]}
                    icon={
                      createStationIcon(
                        station.status
                      )
                    }
                    eventHandlers={{
                      click: () =>
                        openStation(
                          station
                        ),
                    }}
                  />

                )
              )}

            </MapContainer>
            <p className="map-helper-text">
  Click a station to open detailed station details
</p>

          </div>

        </div>


        {/* =================================================
            CURRENT STATION
        ================================================= */}

        <div className="station-panel">

          <div className="panel-header">

            <div>

              <h2>
                Current Station
              </h2>

              <p>
                Latest sensor information
              </p>

            </div>

          </div>


          {selectedStation ? (

            <div className="current-station-card">

              {/* STATION HEADER */}

              <div className="station-heading">

                <div className="station-weather-icon">

                  {getWeatherIcon(
                    Number(
                      selectedStation.temperature
                    )
                  )}

                </div>

                <div className="station-title">

                  <h2 className="current-station-name">

                    {selectedStation.district}

                  </h2>

                  <p className="station-type">

                    Automatic Weather Station

                  </p>

                </div>


                <div
                  className={`station-status ${
                    selectedStation.status ===
                    "ANOMALY"
                      ? "status-anomaly"
                      : "status-healthy"
                  }`}
                >

                  <span></span>

                  {selectedStation.status ===
                  "ANOMALY"
                    ? "Anomaly Detected"
                    : "Station Healthy"}

                </div>

              </div>


              {/* SENSOR READINGS */}

              <div className="sensor-grid">

                <div className="sensor-card temperature">

                  <div className="sensor-icon">
                    ♨
                  </div>

                  <div>

                    <span>
                      Temperature
                    </span>

                    <strong>
                      {selectedStation.temperature}°C
                    </strong>

                    <small>
                      Expected:{" "}
                      {
                        selectedStation.expected_temperature
                      }°C
                    </small>

                  </div>

                </div>


                <div className="sensor-card humidity">

                  <div className="sensor-icon">
                    💧
                  </div>

                  <div>

                    <span>
                      Humidity
                    </span>

                    <strong>
                      {selectedStation.humidity}%
                    </strong>

                    <small>
                      Relative humidity
                    </small>

                  </div>

                </div>


                <div className="sensor-card pressure">

                  <div className="sensor-icon">
                    ◉
                  </div>

                  <div>

                    <span>
                      Pressure
                    </span>

                    <strong>
                      {selectedStation.pressure} hPa
                    </strong>

                    <small>
                      Atmospheric pressure
                    </small>

                  </div>

                </div>


                <div className="sensor-card score">

                  <div className="sensor-icon">
                    ∿
                  </div>

                  <div>

                    <span>
                      Anomaly Score
                    </span>

                    <strong>
                      {selectedStation.score}
                    </strong>

                    <small>
                      Isolation Forest
                    </small>

                  </div>

                </div>

              </div>


              {/* FAULT TYPE */}

              <div className="fault-type-card">

                <div className="fault-type-icon">
                  !
                </div>

                <div>

                  <span>
                    FAULT TYPE
                  </span>

                  <strong>
                    {
                      selectedStation.fault ||
                      "NONE"
                    }
                  </strong>

                  <small>
                    {
                      selectedStation.fault
                        ? "Gradual sensor drift detected"
                        : "No active sensor fault"
                    }
                  </small>

                </div>

              </div>


              {/* ANOMALY ALERT */}

              {selectedStation.status ===
                "ANOMALY" && (

                <div className="fault-alert">

                  <div className="alert-icon">
                    !
                  </div>

                  <div>

                    <strong>
                      Sensor anomaly detected
                    </strong>

                    <p>

                      {
                        selectedStation.fault
                      }{" "}
                      fault detected at this station.

                    </p>

                  </div>

                </div>

              )}


              {/* FOOTER */}

              <div className="station-card-footer">

                <div className="last-updated">

                  Last updated:{" "}

                  <strong>
                    {
                      selectedStation.time
                    }
                  </strong>

                </div>

                <button
                  className="station-details-button"
                  onClick={() =>
                    openStation(
                      selectedStation
                    )
                  }
                >

                  View Station Details

                  <span>
                    →
                  </span>

                </button>

              </div>

            </div>

          ) : (

            <div className="no-station">

              <p>
                Select a station from the map
                to view its latest information.
              </p>

            </div>

          )}

        </div>

      </section>


      {/* =================================================
          ACTIVE ALERTS
      ================================================= */}

      <section className="alerts-section">

        <div className="panel-header">

          <div>

            <h2>
              Active Alerts
            </h2>

            <p>
              Stations requiring attention
            </p>

          </div>

          <div className="alert-count">
            {alerts.length} active
          </div>

        </div>


        {alerts.length === 0 ? (

          <div className="no-alerts">

            <div className="no-alert-icon">
              ✓
            </div>

            <div>

              <strong>
                All stations operating normally
              </strong>

              <p>
                No active sensor anomalies detected.
              </p>

            </div>

          </div>

        ) : (

          <div className="alerts-table">

            {/* TABLE HEADER */}

            <div className="alert-table-header">

              <span>
                STATION
              </span>

              <span>
                FAULT TYPE
              </span>

              <span>
                TEMPERATURE
              </span>

              <span>
                TIME
              </span>

              <span>
                ACTION
              </span>

            </div>


            {/* ALERT ROWS */}

            {alerts.map(
              (alert, index) => (

                <button
                  key={`${alert.district}-${index}`}
                  className="alert-row"
                  onClick={() => {

                    const station =
                      stations.find(
                        (item) =>
                          item.district ===
                          alert.district
                      );

                    if (station) {
                      openStation(
                        station
                      );
                    }

                  }}
                >

                  <div className="alert-station">

                    <div className="alert-status-icon">
                      !
                    </div>

                    <strong>
                      {alert.district}
                    </strong>

                  </div>


                  <div className="alert-fault">

                    {alert.fault}

                  </div>


                  <div className="alert-temperature">

                    {alert.temperature}°C

                  </div>


                  <div className="alert-time">

                    {alert.time}

                  </div>


                  <div className="alert-arrow">

                    →

                  </div>

                </button>

              )
            )}

          </div>

        )}

      </section>


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="dashboard-footer">

        <span>
          WeatherGuard AI
        </span>

        <span>
          Intelligent AWS Monitoring
        </span>

        <span>
          Isolation Forest • Real-time anomaly detection
        </span>

      </footer>

    </div>
  );
}

export default Dashboard;