import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

import "./index.css";


// =========================================================
// API
// =========================================================

const API = "http://127.0.0.1:5000";


// =========================================================
// STATION ICON
// =========================================================

const createStationIcon = (status) => {

  let color = "#16a34a";

  if (status === "ANOMALY") {
    color = "#dc2626";
  }

  if (status === "WARNING") {
    color = "#eab308";
  }

  return L.divIcon({
    className: "custom-marker",

    html: `
      <div
        style="
          width:18px;
          height:18px;
          background:${color};
          border:3px solid white;
          border-radius:50%;
          box-shadow:0 2px 8px rgba(0,0,0,0.35);
        "
      ></div>
    `,

    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
};


// =========================================================
// APP
// =========================================================

function App() {

  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);

  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [summary, setSummary] = useState({
    totalStations: 0,
    healthyStations: 0,
    anomalyStations: 0,
    spike: 0,
    stuck: 0,
    drift: 0,
  });

  const [error, setError] = useState("");


// =========================================================
// FETCH STATIONS
// =========================================================

  const fetchStations = async () => {

    try {

      const response = await fetch(`${API}/api/stations`);

      if (!response.ok) {
        throw new Error("Could not load stations");
      }

      const data = await response.json();

      console.log("STATIONS:", data);

      setStations(data);

      if (data.length > 0) {

        setSelectedStation((previous) => {

          if (!previous) {
            return data[0];
          }

          const updated = data.find(
            (station) =>
              station.district === previous.district
          );

          return updated || data[0];

        });

      }

      setError("");

    } catch (err) {

      console.error(err);

      setError(
        "Unable to connect to WeatherGuard AI backend."
      );

    }

  };


// =========================================================
// FETCH SUMMARY
// =========================================================

  const fetchSummary = async () => {

    try {

      const response = await fetch(
        `${API}/api/summary`
      );

      if (!response.ok) {
        throw new Error("Summary unavailable");
      }

      const data = await response.json();

      console.log("SUMMARY:", data);

      setSummary(data);

    } catch (err) {

      console.error("Summary error:", err);

    }

  };


// =========================================================
// FETCH ALERTS
// =========================================================

  const fetchAlerts = async () => {

    try {

      const response = await fetch(
        `${API}/api/alerts`
      );

      if (!response.ok) {
        throw new Error("Alerts unavailable");
      }

      const data = await response.json();

      console.log("ALERTS:", data);

      setAlerts(data);

    } catch (err) {

      console.error("Alerts error:", err);

    }

  };


// =========================================================
// INITIAL DATA
// =========================================================

  useEffect(() => {

    fetchStations();
    fetchSummary();
    fetchAlerts();

    const interval = setInterval(() => {

      fetchStations();
      fetchSummary();
      fetchAlerts();

    }, 3000);

    return () => clearInterval(interval);

  }, []);


// =========================================================
// FETCH HISTORY
// =========================================================

  useEffect(() => {

    if (!selectedStation) {
      return;
    }

    const district = selectedStation.district;

    const fetchHistory = async () => {

      try {

        const response = await fetch(
          `${API}/api/history/${encodeURIComponent(district)}`
        );

        if (!response.ok) {
          throw new Error("History unavailable");
        }

        const data = await response.json();

        console.log(
          `HISTORY ${district}:`,
          data
        );

        setHistory(data);

      } catch (err) {

        console.error(
          "History error:",
          err
        );

        setHistory([]);

      }

    };

    fetchHistory();

    const interval = setInterval(
      fetchHistory,
      3000
    );

    return () => clearInterval(interval);

  }, [selectedStation?.district]);


// =========================================================
// FORMAT STATUS
// =========================================================

  const getHealthClass = (status) => {

    if (status === "ANOMALY") {
      return "danger";
    }

    if (status === "WARNING") {
      return "warning";
    }

    return "healthy";

  };


// =========================================================
// RENDER
// =========================================================

  return (

    <div className="dashboard">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="top-header">

        <div>

          <h1>
            WeatherGuard AI
          </h1>

          <p>
            Intelligent Automatic Weather Station Monitoring
          </p>

        </div>

        <div className="live-indicator">

          <span className="live-dot"></span>

          Live Monitoring

        </div>

      </header>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div className="error-message">
          {error}
        </div>

      )}


      {/* =================================================
          KPI CARDS
      ================================================= */}

      <section className="kpi-grid">

        <div className="kpi-card">

          <span className="kpi-label">
            TOTAL STATIONS
          </span>

          <strong>
            {summary.totalStations}
          </strong>

          <small>
            Monitoring network
          </small>

        </div>


        <div className="kpi-card normal-kpi">

          <span className="kpi-label">
            HEALTHY
          </span>

          <strong>
            {summary.healthyStations}
          </strong>

          <small>
            Normal stations
          </small>

        </div>


        <div className="kpi-card anomaly-kpi">

          <span className="kpi-label">
            ANOMALIES
          </span>

          <strong>
            {summary.anomalyStations}
          </strong>

          <small>
            Stations requiring attention
          </small>

        </div>


        <div className="kpi-card anomaly-kpi">

          <span className="kpi-label">
            SPIKE FAULTS
          </span>

          <strong>
            {summary.spike}
          </strong>

          <small>
            Sudden changes
          </small>

        </div>


        <div className="kpi-card warning-kpi">

          <span className="kpi-label">
            STUCK FAULTS
          </span>

          <strong>
            {summary.stuck}
          </strong>

          <small>
            Repeated readings
          </small>

        </div>


        <div className="kpi-card warning-kpi">

          <span className="kpi-label">
            DRIFT FAULTS
          </span>

          <strong>
            {summary.drift}
          </strong>

          <small>
            Gradual sensor drift
          </small>

        </div>

      </section>


      {/* =================================================
          MAP + CURRENT STATION
      ================================================= */}

      <section className="main-monitor-grid">


        {/* MAP */}

        <div className="panel map-panel">

          <div className="panel-header">

            <div>

              <h2>
                Weather Station Network
              </h2>

              <p>
                Real-time station health monitoring
              </p>

            </div>

            <span className="station-count">
              {stations.length} stations
            </span>

          </div>


          <div className="map-wrapper">

            <MapContainer
              center={[17.8, 78.5]}
              zoom={7}
              className="weather-map"
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />


              {stations.map((station) => (

                <Marker
                  key={station.district}
                  position={[
                    station.lat,
                    station.lon
                  ]}
                  icon={createStationIcon(
                    station.status
                  )}
                  eventHandlers={{
                    click: () => {
                      setSelectedStation(station);
                    },
                  }}
                >

                  <Popup>

                    <div className="popup">

                      <h3>
                        {station.district}
                      </h3>

                      <p>
                        <strong>
                          Temperature:
                        </strong>{" "}
                        {station.temperature} °C
                      </p>

                      <p>
                        <strong>
                          Humidity:
                        </strong>{" "}
                        {station.humidity} %
                      </p>

                      <p>
                        <strong>
                          Pressure:
                        </strong>{" "}
                        {station.pressure} hPa
                      </p>

                      <p>
                        <strong>
                          Status:
                        </strong>{" "}
                        {station.status}
                      </p>

                      <p>
                        <strong>
                          Fault:
                        </strong>{" "}
                        {station.fault}
                      </p>

                    </div>

                  </Popup>

                </Marker>

              ))}

            </MapContainer>

          </div>


          <div className="map-legend">

            <div>
              <span className="legend-circle green"></span>
              Healthy
            </div>

            <div>
              <span className="legend-circle yellow"></span>
              Warning
            </div>

            <div>
              <span className="legend-circle red"></span>
              Anomaly
            </div>

          </div>

        </div>


        {/* CURRENT STATION */}

        <div className="panel station-panel">

          <div className="panel-header">

            {selectedStation ? (

              <div className="station-title">

                <div>

                  <h3>
                    {selectedStation.district}
                  </h3>

                  <p>
                    Automatic Weather Station
                  </p>

                </div>

              </div>

            ) : (

              <div>

                <h2>
                  Current Station
                </h2>

                <p>
                  Waiting for station data
                </p>

              </div>

            )}

          </div>


          {selectedStation ? (

            <>

              {/* HEALTH */}

              <div
                className={`station-health ${getHealthClass(
                  selectedStation.status
                )}`}
              >

                <span className="health-dot"></span>

                <div>

                  <strong>
                    {selectedStation.status ===
                    "ANOMALY"
                      ? "Anomaly Detected"
                      : "Station Healthy"}
                  </strong>

                  <small>
                    Sensor monitoring active
                  </small>

                </div>

              </div>


              {/* READINGS */}

              <div className="current-readings">

                <div className="current-reading">

                  <span>
                    Temperature
                  </span>

                  <strong>
                    {selectedStation.temperature} °C
                  </strong>

                  <small>
                    Expected{" "}
                    {selectedStation.expected_temperature}
                    °C
                  </small>

                </div>


                <div className="current-reading">

                  <span>
                    Humidity
                  </span>

                  <strong>
                    {selectedStation.humidity} %
                  </strong>

                  <small>
                    Relative humidity
                  </small>

                </div>


                <div className="current-reading">

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


                <div className="current-reading">

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


              {/* DETAILS */}

              <div className="station-details">

                <div>

                  <span>
                    Fault Type
                  </span>

                  <strong>
                    {selectedStation.fault}
                  </strong>

                </div>


                <div>

                  <span>
                    Status
                  </span>

                  <strong
                    className={
                      selectedStation.status ===
                      "ANOMALY"
                        ? "danger-text"
                        : "success-text"
                    }
                  >
                    {selectedStation.status}
                  </strong>

                </div>


                <div>

                  <span>
                    Last Reading
                  </span>

                  <strong>
                    {selectedStation.time}
                  </strong>

                </div>

              </div>


              {/* FAULT ALERT */}

              {selectedStation.status ===
                "ANOMALY" && (

                <div className="fault-alert">

                  <div className="fault-icon">
                    !
                  </div>

                  <div>

                    <strong>
                      Sensor anomaly detected
                    </strong>

                    <p>
                      {selectedStation.fault !==
                      "NONE"
                        ? `${selectedStation.fault} fault detected at this station.`
                        : "Isolation Forest detected an abnormal weather reading."}
                    </p>

                  </div>

                </div>

              )}


              <div className="last-update">

                Last updated:{" "}
                {selectedStation.time}

              </div>

            </>

          ) : (

            <div className="loading">
              Loading station data...
            </div>

          )}

        </div>

      </section>


      {/* =================================================
          CHARTS
      ================================================= */}

      <section className="charts-grid">


        {/* TEMPERATURE */}

       <div className="chart-box">
  <LineChart
    width={600}
    height={280}
    data={history}
    margin={{ top: 10, right: 20, left: 20, bottom: 10 }}
  >
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="time" />
    <YAxis />
    <Tooltip />
    <Line
      type="monotone"
      dataKey="temperature"
      stroke="#2563eb"
      strokeWidth={2}
      dot={false}
    />
  </LineChart>
</div>


        {/* HUMIDITY */}

       <div className="chart-box">
  {history.length === 0 ? (
    <div className="chart-empty">
      No humidity data available
    </div>
  ) : (
    <LineChart
      width={600}
      height={280}
      data={history}
      margin={{ top: 10, right: 20, left: 20, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="time" />
      <YAxis />
      <Tooltip />
      <Line
        type="monotone"
        dataKey="humidity"
        stroke="#16a34a"
        strokeWidth={2}
        dot={false}
      />
    </LineChart>
  )}
</div>
</section>

      {/* =================================================
          ALERTS
      ================================================= */}

      <section className="panel alerts-panel">

        <div className="panel-header">

          <div>

            <h2>
              Active Alerts
            </h2>

            <p>
              Stations requiring attention
            </p>

          </div>

          <span className="alert-count">
            {alerts.length} active
          </span>

        </div>


        {alerts.length === 0 ? (

          <div className="no-alerts">
            ✓ No active sensor anomalies
          </div>

        ) : (

          <div className="table-wrapper">

            <table>

              <thead>

                <tr>

                  <th>
                    District
                  </th>

                  <th>
                    Fault Type
                  </th>

                  <th>
                    Temperature
                  </th>

                  <th>
                    Time
                  </th>

                  <th>
                    Status
                  </th>

                </tr>

              </thead>


              <tbody>

                {alerts.map(
                  (alert, index) => (

                    <tr key={index}>

                      <td>
                        {alert.district}
                      </td>

                      <td>

                        <span
                          className={`fault-badge ${alert.fault.toLowerCase()}`}
                        >
                          {alert.fault}
                        </span>

                      </td>

                      <td>
                        {alert.temperature} °C
                      </td>

                      <td>
                        {alert.time}
                      </td>

                      <td>

                        <span className="status-danger">
                          ANOMALY
                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer>

        <span>
          WeatherGuard AI • Intelligent AWS Monitoring
        </span>

        <span>
          Powered by Isolation Forest
        </span>

      </footer>

    </div>

  );

}

export default App;