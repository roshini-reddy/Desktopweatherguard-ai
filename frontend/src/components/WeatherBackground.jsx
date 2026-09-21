function WeatherBackground({
  status,
  fault,
  temperature,
}) {
  let weatherType = "clear";

  if (fault === "SPIKE") {
    weatherType = "storm";
  } else if (fault === "DRIFT") {
    weatherType = "rain";
  } else if (fault === "STUCK") {
    weatherType = "cloud";
  } else if (status === "ANOMALY") {
    weatherType = "storm";
  } else if (
    temperature !== undefined &&
    temperature >= 35
  ) {
    weatherType = "hot";
  }

  return (
    <div
      className={`weather-background weather-${weatherType}`}
    >

      <div className="weather-gradient"></div>

      <div className="weather-cloud cloud-a">
        ☁
      </div>

      <div className="weather-cloud cloud-b">
        ☁
      </div>

      <div className="weather-cloud cloud-c">
        ☁
      </div>

      {weatherType === "rain" && (
        <div className="rain-layer">
          {Array.from(
            { length: 35 },
            (_, index) => (
              <span
                key={index}
                className="rain-drop"
                style={{
                  left: `${(
                    (index * 29) % 100
                  )}%`,
                  animationDelay: `${
                    (index % 10) * 0.15
                  }s`,
                }}
              />
            )
          )}
        </div>
      )}

      {weatherType === "storm" && (
        <div className="storm-glow"></div>
      )}

      {weatherType === "hot" && (
        <div className="sun-glow">
          ☀
        </div>
      )}

    </div>
  );
}

export default WeatherBackground;