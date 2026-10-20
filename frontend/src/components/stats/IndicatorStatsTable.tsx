import { INDICATOR_KEYS, INDICATOR_TEXT, LABEL_TEXT, formatNumber } from "@/lib/format";
import type { ClassStats } from "@/lib/types";

export function IndicatorStatsTable({ classes }: { classes: ClassStats[] }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <caption className="sr-only">Indicator statistics per dataset class</caption>
        <thead>
          <tr>
            <th scope="col">Indicator</th>
            <th scope="col">Class</th>
            <th scope="col">n</th>
            <th scope="col">Mean</th>
            <th scope="col">Median</th>
            <th scope="col">Std</th>
            <th scope="col">Min</th>
            <th scope="col">Max</th>
          </tr>
        </thead>
        <tbody>
          {INDICATOR_KEYS.flatMap((key) =>
            classes.map((item, index) => {
              const stats = item.indicators[key];
              const digits = INDICATOR_TEXT[key].unit === "D" ? 2 : 1;
              return (
                <tr key={`${key}-${item.label}`} className={index === 0 ? "row--group" : undefined}>
                  {index === 0 && (
                    <th scope="rowgroup" rowSpan={classes.length}>
                      {INDICATOR_TEXT[key].name} ({INDICATOR_TEXT[key].unit})
                    </th>
                  )}
                  <td>{LABEL_TEXT[item.label]}</td>
                  <td>{stats.n}</td>
                  <td>{formatNumber(stats.mean, digits)}</td>
                  <td>{formatNumber(stats.median, digits)}</td>
                  <td>{formatNumber(stats.std, digits)}</td>
                  <td>{formatNumber(stats.min, digits)}</td>
                  <td>{formatNumber(stats.max, digits)}</td>
                </tr>
              );
            }),
          )}
        </tbody>
      </table>
    </div>
  );
}
