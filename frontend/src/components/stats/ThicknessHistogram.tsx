"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { LABEL_TEXT } from "@/lib/format";
import type { ClassStats, Label } from "@/lib/types";
import { LABEL_COLORS } from "./chartColors";

type Row = { from: number; range: string } & Partial<Record<Label, number>>;

export function mergeHistograms(classes: ClassStats[]): { rows: Row[]; binWidth: number } {
  const binWidth = classes[0]?.histograms.min_thickness_um.bin_width ?? 20;
  const rows = new Map<number, Row>();
  for (const item of classes) {
    for (const bin of item.histograms.min_thickness_um.bins) {
      const row = rows.get(bin.from) ?? {
        from: bin.from,
        range: `${bin.from}–${bin.from + binWidth - 1}`,
      };
      row[item.label] = bin.count;
      rows.set(bin.from, row);
    }
  }
  const sorted = [...rows.values()].sort((a, b) => a.from - b.from);
  return { rows: sorted, binWidth };
}

export function ThicknessHistogram({ classes }: { classes: ClassStats[] }) {
  const { rows } = mergeHistograms(classes);
  if (rows.length === 0) {
    return <p className="muted">No thickness values available.</p>;
  }
  return (
    <div
      className="chart"
      role="img"
      aria-label="Histogram of visible minimum thickness in micrometres, one series per class"
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 24, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="range"
            interval="preserveStartEnd"
            label={{ value: "Visible min thickness (µm)", position: "insideBottom", offset: -12 }}
          />
          <YAxis
            allowDecimals={false}
            label={{ value: "Exams", angle: -90, position: "insideLeft" }}
          />
          <Tooltip />
          <Legend verticalAlign="top" />
          {classes.map((item) => (
            <Bar
              key={item.label}
              dataKey={item.label}
              name={LABEL_TEXT[item.label]}
              fill={LABEL_COLORS[item.label]}
              isAnimationActive={false}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
