"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { LABEL_TEXT } from "@/lib/format";
import type { ClassStats } from "@/lib/types";
import { LABEL_COLORS } from "./chartColors";

export function ClassCountChart({ classes }: { classes: ClassStats[] }) {
  const data = classes.map((item) => ({
    label: item.label,
    name: LABEL_TEXT[item.label],
    exams: item.exams,
  }));
  return (
    <div
      className="chart"
      role="img"
      aria-label={`Exams per class: ${data.map((d) => `${d.name} ${d.exams}`).join(", ")}`}
    >
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="exams" name="Exams" isAnimationActive={false}>
            {data.map((entry) => (
              <Cell key={entry.label} fill={LABEL_COLORS[entry.label]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
