import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { io } from "socket.io-client";
import GlobalCharts from "../../components/GlobalCharts";
import TrustEvolutionChart from "../../components/TrustEvolutionChart";

const SOCKET_URL = "http://127.0.0.1:5000";

export default function ServerDashboard() {
  const [data, setData] = useState(null);
  const [clients, setClients] = useState([]);
  const [logs, setLogs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const socket = io(SOCKET_URL);

    socket.on("connect", () => {
      console.log("Connected to WebSocket server");
    });

    socket.on("server_update", (serverData) => {
      setData(serverData);
    });

    socket.on("clients_update", (clientsData) => {
      setClients(clientsData);
    });

    socket.on("logs_update", (logsData) => {
      setLogs(logsData);
    });

    return () => socket.disconnect();
  }, []);

  if (!data)
    return <div style={{ padding: 20 }}>Waiting for live data...</div>;

  return (
    <div
      style={{
        padding: 30,
        background: "#0f172a",
        color: "white",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ marginBottom: 20 }}>Server Dashboard (Live)</h1>

      {/* Stats Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 20,
          marginBottom: 30,
        }}
      >
        <StatCard title="Round" value={data.round} />
        <StatCard
          title="Accuracy"
          value={data.global_accuracy.toFixed(4)}
        />
        <StatCard title="Loss" value={data.global_loss.toFixed(4)} />
        <StatCard
          title="Rejected Updates"
          value={data.rejected_updates}
        />
      </div>

      {/* Charts */}
      <div style={{ marginBottom: 40 }}>
        <GlobalCharts
          round={data.round}
          accuracy={data.global_accuracy}
          loss={data.global_loss}
        />
      </div>

      {/* Trust Evolution */}
      <div style={{ marginBottom: 40 }}>
        <TrustEvolutionChart clients={clients} />
      </div>

      {/* DP Parameters */}
      <div
        style={{
          background: "#1e293b",
          padding: 20,
          borderRadius: 10,
          marginBottom: 30,
        }}
      >
        <h2>Differential Privacy</h2>
        <p>Noise Sigma: {data.dp_sigma}</p>
        <p>Clip Norm: {data.clip_norm}</p>
      </div>

      {/* Trust Table */}
      <h2>Client Trust & Async Monitoring</h2>
      <div style={{ overflowX: "auto", marginBottom: 40 }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "#1e293b",
          }}
        >
          <thead>
            <tr>
              <th style={thStyle}>Client ID</th>
              <th style={thStyle}>Trust Score</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Staleness</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => {
              const stalenessColor =
                c.staleness <= 1
                  ? "lightgreen"
                  : c.staleness <= 3
                  ? "orange"
                  : "red";

              return (
                <tr
                  key={c.id}
                  style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/server/client/${c.id}`)}
                >
                  <td style={tdStyle}>{c.id}</td>
                  <td style={tdStyle}>{c.trust.toFixed(3)}</td>
                  <td
                    style={{
                      ...tdStyle,
                      color:
                        c.status === "malicious"
                          ? "red"
                          : "lightgreen",
                    }}
                  >
                    {c.status}
                  </td>
                  <td
                    style={{
                      ...tdStyle,
                      color: stalenessColor,
                      fontWeight: "bold",
                    }}
                  >
                    {c.staleness}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Logs */}
      <h2>Aggregation Logs</h2>
      <div
        style={{
          background: "#1e293b",
          padding: 15,
          borderRadius: 8,
          maxHeight: 200,
          overflowY: "auto",
        }}
      >
        {logs.map((log, index) => (
          <div key={index} style={{ marginBottom: 5 }}>
            {log}
          </div>
        ))}
      </div>
    </div>
  );
}

/* Reusable Stat Card */
function StatCard({ title, value }) {
  return (
    <div
      style={{
        background: "#1e293b",
        padding: 20,
        borderRadius: 10,
        textAlign: "center",
      }}
    >
      <h3 style={{ marginBottom: 10 }}>{title}</h3>
      <p style={{ fontSize: 22, fontWeight: "bold" }}>{value}</p>
    </div>
  );
}

const thStyle = {
  padding: 10,
  borderBottom: "1px solid #334155",
  textAlign: "left",
};

const tdStyle = {
  padding: 10,
  borderBottom: "1px solid #334155",
};