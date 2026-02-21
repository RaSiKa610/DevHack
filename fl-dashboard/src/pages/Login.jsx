import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

export default function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = (role) => {
    login(role);
    navigate(role === "server" ? "/server" : "/client");
  };

  return (
    <div style={{ height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "#0f172a", color: "white" }}>
      <div style={{ padding: 40, background: "#1e293b", borderRadius: 10 }}>
        <h2>Federated Learning System</h2>
        <button onClick={() => handleLogin("server")} style={{ margin: 10 }}>Login as Server</button>
        <button onClick={() => handleLogin("client")} style={{ margin: 10 }}>Login as Client</button>
      </div>
    </div>
  );
}