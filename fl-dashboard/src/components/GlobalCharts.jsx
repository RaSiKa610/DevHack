import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { useState, useEffect } from "react";

export default function GlobalCharts({ round, accuracy, loss }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    if (round !== undefined) {
      setData(prev => [
        ...prev,
        { round, accuracy, loss }
      ]);
    }
  }, [round, accuracy, loss]);

  return (
    <div style={{ display: "flex", gap: 30 }}>
      <LineChart width={500} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="round" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="accuracy" stroke="#00ffcc" />
        <Line type="monotone" dataKey="loss" stroke="#ff4d4d" />
      </LineChart>
    </div>
  );
}