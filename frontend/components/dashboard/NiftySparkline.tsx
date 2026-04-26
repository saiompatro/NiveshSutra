"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  Tooltip,
  YAxis,
} from "recharts";

interface NiftySparklineProps {
  data: { date: string; close: number }[];
}

export function NiftySparkline({ data }: NiftySparklineProps) {
  if (!data.length) return null;

  const first = data[0].close;
  const last = data[data.length - 1].close;
  const isUp = last >= first;
  const color = isUp ? "#34d399" : "#f87171";

  return (
    <ResponsiveContainer width="100%" height={64}>
      <LineChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 4 }}>
        <YAxis domain={["auto", "auto"]} hide />
        <Tooltip
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            fontSize: "12px",
            color: "hsl(var(--foreground))",
          }}
          formatter={(val) => [`₹${Number(val).toLocaleString("en-IN")}`, "Nifty 50"]}
          labelFormatter={(label) => label}
        />
        <Line
          type="monotone"
          dataKey="close"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
