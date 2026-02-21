import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import ServerDashboard from "./pages/server/ServerDashboard";
import ClientDashboard from "./pages/client/ClientDashboard";
import ClientDetails from "./pages/server/ClientDetails";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./routes/ProtectedRoute";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />

          <Route
            path="/server"
            element={
              <ProtectedRoute allowedRole="server">
                <ServerDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/client"
            element={
              <ProtectedRoute allowedRole="client">
                <ClientDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/server/client/:id"
            element={
              <ProtectedRoute allowedRole="server">
                <ClientDetails />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;