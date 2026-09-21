import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    if (username === "operator" && password === "weatherguard") {
      localStorage.setItem("weatherguard_logged_in", "true");
      navigate("/dashboard");
    } else {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="login-page">

      {/* ================= BACKGROUND ================= */}

      <div className="sky-background">

        {/* Sun */}
        <div className="sun-glow">
          <div className="sun-core"></div>
        </div>

        {/* Large technology globe */}
        <div className="tech-globe">
          <div className="globe-grid"></div>

          <div className="globe-orbit orbit-1"></div>
          <div className="globe-orbit orbit-2"></div>
          <div className="globe-orbit orbit-3"></div>

          <span className="globe-dot dot-1"></span>
          <span className="globe-dot dot-2"></span>
          <span className="globe-dot dot-3"></span>
        </div>

        {/* Curved technology lines */}
        <div className="orbit-line line-one"></div>
        <div className="orbit-line line-two"></div>
        <div className="orbit-line line-three"></div>

        {/* Atmospheric glow */}
        <div className="atmosphere"></div>

        {/* Clouds */}
        <div className="cloud cloud-left">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <div className="cloud cloud-right">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <div className="cloud cloud-bottom">
          <span></span>
          <span></span>
          <span></span>
        </div>

        {/* Bottom flowing waves */}
        <div className="wave wave-1"></div>
        <div className="wave wave-2"></div>
        <div className="wave wave-3"></div>

      </div>

      {/* ================= TOP BRAND ================= */}

      <header className="login-top-header">

        <div className="brand-block">

          <div className="brand-weather-icon">
            <span className="brand-sun"></span>
            <span className="brand-cloud"></span>
          </div>

          <div>
            <h1>WeatherGuard AI</h1>
            <p>Intelligent Automatic Weather Station Monitoring</p>
          </div>

        </div>

        <div className="live-monitoring">

          <span className="live-dot"></span>

          <div>
            <strong>LIVE MONITORING</strong>
            <small>Weather intelligence system</small>
          </div>

        </div>

      </header>

      {/* ================= LEFT MESSAGE ================= */}

      <div className="left-message">

        <div className="message-item">
          <strong>MONITOR</strong>
          <span></span>
        </div>

        <div className="message-item">
          <strong>DETECT</strong>
          <span></span>
        </div>

        <div className="message-item">
          <strong>PROTECT</strong>
          <span></span>
        </div>

      </div>

      {/* ================= LOGIN CARD ================= */}

      <main className="login-card">

        <div className="login-card-inner">

          {/* Logo */}

          <div className="login-logo">

            <div className="login-sun"></div>

            <div className="login-cloud">
              <span></span>
              <span></span>
            </div>

          </div>

          {/* Heading */}

          <h2>WeatherGuard AI</h2>

          <p className="login-subtitle">
            Intelligent Automatic Weather Station Monitoring
          </p>

          {/* Form */}

          <form onSubmit={handleLogin}>

            {/* Username */}

            <div className="input-group">

              <label htmlFor="username">
                Username
              </label>

              <div className="input-wrapper">

                <span className="input-icon user-icon">
                  ♙
                </span>

                <input
                  id="username"
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setError("");
                  }}
                  autoComplete="username"
                />

              </div>

            </div>

            {/* Password */}

            <div className="input-group">

              <label htmlFor="password">
                Password
              </label>

              <div className="input-wrapper">

                <span className="input-icon">
                  🔒
                </span>

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError("");
                  }}
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? "◉" : "◌"}
                </button>

              </div>

            </div>

            {/* Error */}

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            {/* Sign in */}

            <button
              type="submit"
              className="signin-button"
            >
              <span>Sign In</span>
              <span className="signin-arrow">→</span>
            </button>

          </form>

          {/* Demo access */}

          <div className="demo-access">

            <span>Demo access:</span>

            <strong>operator</strong>

            <b>/</b>

            <strong>weatherguard</strong>

          </div>

          {/* Footer */}

          <div className="login-divider"></div>

          <div className="login-footer">
            WeatherGuard AI
            <span>•</span>
            AWS Monitoring Platform
          </div>

        </div>

      </main>

    </div>
  );
}

export default Login;