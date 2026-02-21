import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from "recharts";
import { useEffect, useState } from "react";

export default function TrustEvolutionChart({ clients }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    if (!clients.length) return;

    const snapshot = {
      time: new Date().toLocaleTimeString()
    };

    clients.forEach(c => {
      snapshot[`client_${c.id}`] = c.trust;
    });

    setData(prev => [...prev.slice(-20), snapshot]); // keep last 20 points
  }, [clients]);

  return (
    <div style={{
      background: "#1e293b",
      padding: 20,
      borderRadius: 10,
      marginBottom: 40
    }}>
      <h2>Trust Score Evolution</h2>

      <LineChart width={900} height={350} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        <Legend />

        {clients.map((c, index) => (
          <Line
            key={c.id}
            type="monotone"
            dataKey={`client_${c.id}`}
            stroke={`hsl(${index * 70}, 70%, 50%)`}
            dot={false}
          />
        ))}
      </LineChart>
    </div>
  );
}