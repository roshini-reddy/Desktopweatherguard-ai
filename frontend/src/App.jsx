import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import StationDetails from "./pages/StationDetails";


// =========================================================
// PROTECTED ROUTE
// =========================================================

function ProtectedRoute({ children }) {

  const loggedIn =
    localStorage.getItem("weatherguard_logged_in") === "true";

  return loggedIn ? (
    children
  ) : (
    <Navigate
      to="/login"
      replace
    />
  );
}


// =========================================================
// APP
// =========================================================

function App() {

  return (

    <BrowserRouter>

      <Routes>

        {/* =================================================
            LOGIN PAGE
        ================================================= */}

        <Route
          path="/login"
          element={<Login />}
        />


        {/* =================================================
            MAIN DASHBOARD
        ================================================= */}

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            INDIVIDUAL STATION DETAILS
            Example:
            /station/Khammam
            /station/Hyderabad
            /station/Medak
        ================================================= */}

        <Route
          path="/station/:district"
          element={
            <ProtectedRoute>
              <StationDetails />
            </ProtectedRoute>
          }
        />


        {/* =================================================
            ROOT
        ================================================= */}

        <Route
          path="/"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />


        {/* =================================================
            INVALID / UNKNOWN URL
        ================================================= */}

        <Route
          path="*"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />

      </Routes>

    </BrowserRouter>

  );
}


export default App;