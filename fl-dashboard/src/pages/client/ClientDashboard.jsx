import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";

const API = "http://127.0.0.1:5000/api";

export default function ClientDashboard() {
  const [clientData, setClientData] = useState(null);
  const [history, setHistory] = useState([]);

  // For demo assume client id = 1
  const clientId = 1;

  useEffect(() => {
    const fetchClient = async () => {
      try {
        const res = await axios.get(`${API}/client/${clientId}`);
        setClientData(res.data);

        setHistory(prev => [
          ...prev.slice(-20),
          {
            time: new Date().toLocaleTimeString(),
            accuracy: res.data.local_accuracy,
            trust: res.data.trust
          }
        ]);
      } catch (err) {
        console.error("Client API Error:", err);
      }
    };

    fetchClient();
    const interval = setInterval(fetchClient, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!clientData)
    return <div style={{ padding: 20 }}>Loading...</div>;

  return (
    <div style={{
      padding: 30,
      background: "#0f172a",
      color: "white",
      minHeight: "100vh"
    }}>
      <h1 style={{ marginBottom: 20 }}>Client Dashboard</h1>

      {/* Client Stats */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 20,
        marginBottom: 30
      }}>
        <StatCard title="Trust Score" value={clientData.trust.toFixed(3)} />
        <StatCard title="Update Status" value={clientData.update_status} />
        <StatCard title="DP Sigma" value={clientData.dp_sigma} />
        <StatCard title="Local Accuracy" value={clientData.local_accuracy.toFixed(3)} />
      </div>

      {/* Charts */}
      <div style={{
        background: "#1e293b",
        padding: 20,
        borderRadius: 10
      }}>
        <h2>Local Training Evolution</h2>

        <LineChart width={900} height={350} data={history}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="accuracy" stroke="#00ffcc" />
          <Line type="monotone" dataKey="trust" stroke="#ff4d4d" />
        </LineChart>
      </div>
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div style={{
      background: "#1e293b",
      padding: 20,
      borderRadius: 10,
      textAlign: "center"
    }}>
      <h3 style={{ marginBottom: 10 }}>{title}</h3>
      <p style={{ fontSize: 22, fontWeight: "bold" }}>{value}</p>
    </div>
  );
}