import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const API = "http://127.0.0.1:5000/api";

export default function ClientDetails() {
  const { id } = useParams();
  const [clientData, setClientData] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchClient = async () => {
      const res = await axios.get(`${API}/client/${id}`);
      setClientData(res.data);

      setHistory(prev => [
        ...prev.slice(-20),
        {
          time: new Date().toLocaleTimeString(),
          accuracy: res.data.local_accuracy,
          trust: res.data.trust
        }
      ]);
    };

    fetchClient();
    const interval = setInterval(fetchClient, 3000);
    return () => clearInterval(interval);
  }, [id]);

  if (!clientData) return <div style={{ padding: 20 }}>Loading...</div>;

  return (
    <div style={{ padding: 30, background: "#0f172a", color: "white", minHeight: "100vh" }}>
      <h1>Client {id} Detailed Dashboard</h1>

      <p>Trust Score: {clientData.trust.toFixed(3)}</p>
      <p>Update Status: {clientData.update_status}</p>
      <p>DP Sigma: {clientData.dp_sigma}</p>

      <div style={{ marginTop: 30 }}>
        <LineChart width={800} height={350} data={history}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="accuracy" stroke="#00ffcc" />
          <Line type="monotone" dataKey="trust" stroke="#ff4d4d" />
        </LineChart>
      </div>
    </div>
  );
}