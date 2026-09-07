import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from "react-leaflet";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function App() {
  const [summary, setSummary] = useState(null);
  const [latest, setLatest] = useState(null);
  const [weatherData, setWeatherData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const summaryResponse = await fetch(
          "http://127.0.0.1:5000/api/summary"
        );
        const summaryData = await summaryResponse.json();

        const latestResponse = await fetch(
          "http://127.0.0.1:5000/api/latest"
        );
        const latestData = await latestResponse.json();

        const weatherResponse = await fetch(
          "http://127.0.0.1:5000/api/weather"
        );
        const weatherResult = await weatherResponse.json();

        const alertsResponse = await fetch(
          "http://127.0.0.1:5000/api/alerts"
        );
        const alertsData = await alertsResponse.json();

        if (
          !summaryResponse.ok ||
          !latestResponse.ok ||
          !weatherResponse.ok ||
          !alertsResponse.ok
        ) {
          throw new Error("Backend request failed");
        }

        setSummary(summaryData);
        setLatest(latestData);
        setWeatherData(weatherResult);
        setAlerts(alertsData);
        setError("");
      } catch (err) {
        console.error(err);
        setError(
          "Unable to connect to WeatherGuard AI backend."
        );
      }
    };

    fetchDashboardData();

    const interval = setInterval(
      fetchDashboardData,
      3000
    );

    return () => clearInterval(interval);
  }, []);

  const getStationColor = () => {
    if (!latest) return "green";

    if (latest.health_status === "ANOMALY") {
      return "red";
    }

    if (latest.health_status === "WARNING") {
      return "yellow";
    }

    return "green";
  };

  const stationColor = getStationColor();

  const chartData = weatherData.map((item) => {
    const date = new Date(item.datetime);

    return {
      time: `${String(date.getHours()).padStart(2, "0")}:00`,
      temperature: Number(item.T2M),
      humidity: Number(item.RH2M),
    };
  });

  const healthClass =
    latest?.health_status === "ANOMALY"
      ? "danger"
      : latest?.health_status === "WARNING"
      ? "warning"
      : "healthy";

  return (
    <div className="dashboard">

      {/* ================= HEADER ================= */}

      <header className="top-header">

        <div>
          <h1>WeatherGuard AI</h1>
          <p>
            Intelligent Automatic Weather Station
            Anomaly Detection System
          </p>
        </div>

        <div className="live-indicator">
          <span className="live-dot"></span>
          <span>System Active</span>
        </div>

      </header>


      {/* ================= ERROR ================= */}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}


      {/* ================= KPI CARDS ================= */}

      {summary && (
        <section className="kpi-grid">

          <div className="kpi-card normal-kpi">
            <span className="kpi-label">
              NORMAL
            </span>

            <strong>
              {summary.normal}
            </strong>

            <small>
              Healthy readings
            </small>
          </div>


          <div className="kpi-card warning-kpi">
            <span className="kpi-label">
              WARNING
            </span>

            <strong>
              {summary.warnings}
            </strong>

            <small>
              Borderline readings
            </small>
          </div>


          <div className="kpi-card anomaly-kpi">
            <span className="kpi-label">
              ANOMALY
            </span>

            <strong>
              {summary.anomalies}
            </strong>

            <small>
              Detected anomalies
            </small>
          </div>


          <div className="kpi-card">
            <span className="kpi-label">
              SPIKE
            </span>

            <strong>
              {summary.spikes}
            </strong>

            <small>
              Sudden changes
            </small>
          </div>


          <div className="kpi-card">
            <span className="kpi-label">
              STUCK
            </span>

            <strong>
              {summary.stuck}
            </strong>

            <small>
              Sensor stuck
            </small>
          </div>


          <div className="kpi-card">
            <span className="kpi-label">
              DRIFT
            </span>

            <strong>
              {summary.drift}
            </strong>

            <small>
              Gradual changes
            </small>
          </div>

        </section>
      )}


      {/* ================= MAP + CURRENT STATION ================= */}

      <section className="main-monitor-grid">

        {/* MAP */}

        <div className="panel map-panel">

          <div className="panel-header">

            <div>
              <h2>AWS Health Map</h2>

              <p>
                Real-time station monitoring
              </p>
            </div>

            <span className="station-count">
              1 Station Monitored
            </span>

          </div>


          <div className="map-wrapper">

            <MapContainer
              center={[17.385, 78.4867]}
              zoom={10}
              scrollWheelZoom={true}
              className="weather-map"
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />


              <CircleMarker
                center={[17.385, 78.4867]}
                radius={16}
                pathOptions={{
                  color: stationColor,
                  fillColor: stationColor,
                  fillOpacity: 0.85,
                  weight: 4,
                }}
              >

                <Popup>

                  <div className="popup">

                    <h3>
                      Hyderabad AWS
                    </h3>

                    <p>
                      <strong>
                        Health:
                      </strong>{" "}
                      {latest?.health_status}
                    </p>

                    <p>
                      <strong>
                        Temperature:
                      </strong>{" "}
                      {latest
                        ? `${Number(
                            latest.T2M
                          ).toFixed(2)} °C`
                        : "--"}
                    </p>

                    <p>
                      <strong>
                        Humidity:
                      </strong>{" "}
                      {latest
                        ? `${Number(
                            latest.RH2M
                          ).toFixed(2)} %`
                        : "--"}
                    </p>

                    <p>
                      <strong>
                        Pressure:
                      </strong>{" "}
                      {latest
                        ? `${Number(
                            latest.PS
                          ).toFixed(2)} hPa`
                        : "--"}
                    </p>

                    <p>
                      <strong>
                        Fault:
                      </strong>{" "}
                      {latest?.fault_type || "NONE"}
                    </p>

                  </div>

                </Popup>

              </CircleMarker>

            </MapContainer>

          </div>


          <div className="map-legend">

            <div>
              <span className="legend-circle green"></span>
              Normal
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

            <div>
              <h2>Current Station</h2>
              <p>Latest AWS observation</p>
            </div>

          </div>


          {latest ? (

            <>

              <div className={`station-health ${healthClass}`}>

                <span className="health-dot"></span>

                <div>
                  <strong>
                    {latest.health_status}
                  </strong>

                  <small>
                    Hyderabad AWS
                  </small>
                </div>

              </div>


              <div className="current-readings">

                <div className="current-reading">

                  <span>
                    Temperature
                  </span>

                  <strong>
                    {Number(
                      latest.T2M
                    ).toFixed(2)}°C
                  </strong>

                </div>


                <div className="current-reading">

                  <span>
                    Humidity
                  </span>

                  <strong>
                    {Number(
                      latest.RH2M
                    ).toFixed(2)}%
                  </strong>

                </div>


                <div className="current-reading">

                  <span>
                    Pressure
                  </span>

                  <strong>
                    {Number(
                      latest.PS
                    ).toFixed(2)}
                    <small> hPa</small>
                  </strong>

                </div>


                <div className="current-reading">

                  <span>
                    Expected Temp.
                  </span>

                  <strong>
                    {Number(
                      latest.expected_temperature
                    ).toFixed(2)}°C
                  </strong>

                </div>

              </div>


              <div className="station-details">

                <div>
                  <span>ML Detection</span>

                  <strong>
                    {latest.isolation_forest_status}
                  </strong>
                </div>


                <div>
                  <span>Final Status</span>

                  <strong
                    className={
                      latest.final_status === "ANOMALY"
                        ? "danger-text"
                        : "success-text"
                    }
                  >
                    {latest.final_status}
                  </strong>
                </div>


                <div>
                  <span>Fault Type</span>

                  <strong
                    className={
                      latest.fault_type !== "NONE"
                        ? "danger-text"
                        : "success-text"
                    }
                  >
                    {latest.fault_type}
                  </strong>
                </div>


                <div>
                  <span>Anomaly Score</span>

                  <strong>
                    {Number(
                      latest.anomaly_score
                    ).toFixed(4)}
                  </strong>
                </div>

              </div>


              <div className="last-update">

                Last reading:
                {" "}
                {latest.datetime}

              </div>

            </>

          ) : (

            <div className="loading">
              Waiting for AWS data...
            </div>

          )}

        </div>

      </section>


      {/* ================= CHARTS ================= */}

      <section className="charts-grid">

        {/* TEMPERATURE */}

        <div className="panel chart-panel">

          <div className="panel-header">

            <div>
              <h2>Temperature Trend</h2>

              <p>
                AWS temperature over time
              </p>
            </div>

            <span className="chart-unit">
              °C
            </span>

          </div>


          <div className="chart-box">

            {chartData.length > 0 ? (

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <LineChart
                  data={chartData}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 5,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="time"
                  />

                  <YAxis />

                  <Tooltip />

                  <Line
                    type="monotone"
                    dataKey="temperature"
                    name="Temperature"
                    strokeWidth={3}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                  />

                </LineChart>

              </ResponsiveContainer>

            ) : (

              <div className="chart-empty">
                Waiting for readings...
              </div>

            )}

          </div>

        </div>


        {/* HUMIDITY */}

        <div className="panel chart-panel">

          <div className="panel-header">

            <div>
              <h2>Humidity Trend</h2>

              <p>
                Relative humidity over time
              </p>
            </div>

            <span className="chart-unit">
              %
            </span>

          </div>


          <div className="chart-box">

            {chartData.length > 0 ? (

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <LineChart
                  data={chartData}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 5,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="time"
                  />

                  <YAxis
                    domain={[0, 100]}
                  />

                  <Tooltip />

                  <Line
                    type="monotone"
                    dataKey="humidity"
                    name="Humidity"
                    strokeWidth={3}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                  />

                </LineChart>

              </ResponsiveContainer>

            ) : (

              <div className="chart-empty">
                Waiting for readings...
              </div>

            )}

          </div>

        </div>

      </section>


      {/* ================= ALERTS ================= */}

      <section className="panel alerts-panel">

        <div className="panel-header">

          <div>
            <h2>Recent Alerts</h2>

            <p>
              Anomalies requiring maintenance attention
            </p>
          </div>

          <span className="alert-count">
            {alerts.length} Alerts
          </span>

        </div>


        {alerts.length === 0 ? (

          <div className="no-alerts">
            ✓ No active anomalies detected
          </div>

        ) : (

          <div className="table-wrapper">

            <table>

              <thead>

                <tr>

                  <th>Time</th>
                  <th>Station</th>
                  <th>Temperature</th>
                  <th>Humidity</th>
                  <th>Fault</th>
                  <th>ML Detection</th>
                  <th>Status</th>

                </tr>

              </thead>


              <tbody>

                {alerts.map(
                  (alert, index) => (

                    <tr key={index}>

                      <td>
                        {alert.datetime}
                      </td>

                      <td>
                        Hyderabad AWS
                      </td>

                      <td>
                        {Number(
                          alert.T2M
                        ).toFixed(2)} °C
                      </td>

                      <td>
                        {Number(
                          alert.RH2M
                        ).toFixed(2)} %
                      </td>

                      <td>

                        <span
                          className={`fault-badge ${alert.fault_type.toLowerCase()}`}
                        >
                          {alert.fault_type}
                        </span>

                      </td>

                      <td>
                        {alert.isolation_forest_status}
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


      {/* ================= FOOTER ================= */}

      <footer>

        <span>
          WeatherGuard AI
        </span>

        <span>
          Intelligent AWS Monitoring
        </span>

        <span>
          Real-time anomaly detection
        </span>

      </footer>

    </div>
  );
}

export default App;