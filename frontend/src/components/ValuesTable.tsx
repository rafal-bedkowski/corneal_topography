"use client";

import { useState } from "react";
import { STATUS_TEXT } from "@/lib/format";
import type { ExtractedValue } from "@/lib/types";

export function ValuesTable({ values, unit }: { values: ExtractedValue[]; unit: string }) {
  const [showIgnored, setShowIgnored] = useState(false);
  const accepted = values.filter((value) => value.status === "accepted");
  const flagged = values.filter(
    (value) => value.status !== "accepted" && value.status !== "rejected",
  );
  const ignored = values.filter((value) => value.status === "rejected");
  const rows = [...accepted, ...flagged, ...(showIgnored ? ignored : [])];

  return (
    <details className="values">
      <summary>
        Extracted values ({accepted.length} accepted, {flagged.length} flagged)
      </summary>
      {rows.length === 0 ? (
        <p className="muted">No values were extracted from this map.</p>
      ) : (
        <table className="table table--compact">
          <thead>
            <tr>
              <th scope="col">Text read</th>
              <th scope="col">Value</th>
              <th scope="col">Confidence</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((value, index) => (
              <tr
                key={`${value.text}-${index}`}
                className={value.status === "accepted" ? undefined : `row--${value.status}`}
              >
                <td>
                  <code>{value.text}</code>
                </td>
                <td>{value.value === null ? "—" : `${value.value} ${unit}`}</td>
                <td>{Math.round(value.confidence * 100)}%</td>
                <td>{STATUS_TEXT[value.status]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {ignored.length > 0 && (
        <label className="checkbox">
          <input
            type="checkbox"
            checked={showIgnored}
            onChange={(event) => setShowIgnored(event.target.checked)}
          />
          Show {ignored.length} ignored labels (angles, axes, eye marker)
        </label>
      )}
    </details>
  );
}
