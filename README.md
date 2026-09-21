# WeatherGuard AI

**AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS)**

Smart India Hackathon 2026 · PSID: SIH26073 · Ministry of Earth Sciences  
**Team: Team Jarvis**



##  Demo Video

> **Add your demo video here**

**Demo Video:**  
[Watch WeatherGuard AI Demo](https://drive.google.com/file/d/1uqPYi9GoFI7ug46IgVvtDKeZAQM0GjiY/view)

---

##  YouTube Video

> **Add your YouTube video here**

[ Watch the Full YouTube Video](YOUR_YOUTUBE_VIDEO_LINK)

---

##  Live Demo

> **Add your Render deployment link here**

[ Open WeatherGuard AI](https://weatherguard-ai-anjl.onrender.com/login)

---

## Problem Statement

Automatic Weather Stations (AWS) continuously collect important environmental measurements such as temperature, humidity, and atmospheric pressure. These measurements are used for weather monitoring, forecasting, and environmental decision-making.

However, AWS sensors can develop faults such as:

- Sudden abnormal spikes
- Stuck sensor readings
- Gradual sensor drift
- Unusual readings caused by sensor malfunction

When faulty readings are not detected quickly, they can affect the quality and reliability of downstream weather monitoring systems.

The challenge is to develop an intelligent system that can automatically monitor AWS data, identify abnormal sensor behavior, classify possible faults, and provide a clear interface for monitoring station health.

---

## Our Solution

**WeatherGuard AI** is an AI/ML-powered AWS monitoring and anomaly detection system.

The system learns normal weather behavior from historical data using an **Isolation Forest** model and identifies unusual sensor readings.

Instead of only showing whether a reading is abnormal, WeatherGuard AI also applies temporal fault-detection logic to identify patterns such as:

- **SPIKE** — sudden abnormal change in sensor reading
- **STUCK** — sensor value remains nearly unchanged
- **DRIFT** — sensor value gradually moves away from expected behavior

The detected information is presented through an interactive web dashboard containing:

- Live station status
- Interactive geographical map
- Weather measurements
- Active alerts
- Fault classification
- Station-level historical graphs
- Simulation controls for testing the ML pipeline

---

## Key Features

### AI-Based Anomaly Detection

Uses an **Isolation Forest** model from scikit-learn to detect unusual sensor behavior without requiring a large labelled fault dataset.

###  Multi-Parameter Monitoring

The system monitors:

- Temperature
- Relative Humidity
- Atmospheric Pressure

###  Fault Detection

The system identifies common sensor-fault patterns:

- **Spike**
- **Stuck**
- **Drift**
- **Unclassified anomaly**

###  Time-Aware Detection

Weather behavior changes according to:

- Hour of the day
- Month / seasonal patterns
- Recent sensor behavior

The system uses historical climatology and time-based features instead of relying only on fixed thresholds.

###  Interactive Weather Station Map

The dashboard uses **Leaflet.js** to display weather stations geographically.

Stations can be selected to open detailed station information.

###  Data Visualization

Station measurements and historical trends are visualized using interactive charts.

###  Monitoring Dashboard

The React dashboard provides:

- Total station count
- Healthy stations
- Anomalous stations
- Fault counts
- Active alerts
- Station locations
- Sensor measurements
- Station details

###  Fault Simulation

A multi-station simulation environment generates realistic normal weather readings and controlled fault scenarios.

This allows the complete anomaly-detection pipeline to be demonstrated without requiring a live AWS sensor network.

###  Cloud Deployment

The application is deployed using:

- **Render** for the Flask backend
- **Render** for the React frontend

---

## How It Works

```text
Historical Weather Data
          ↓
Data Cleaning & Preprocessing
          ↓
Feature Engineering
          ↓
Time-Based Climatology
          ↓
Isolation Forest
          ↓
Anomaly Detection
          ↓
Fault Identification
          ↓
Flask API
          ↓
React Dashboard
          ↓
Station Monitoring & Alerts
