"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { getStats } from "@/lib/api";
import { LABEL_TEXT, SPLIT_TEXT } from "@/lib/format";
import { SPLITS, type Split } from "@/lib/types";
import { Disclaimer } from "./Notice";
import { ErrorState, Loading } from "./StateViews";
import { ClassCountChart } from "./stats/ClassCountChart";
import { ExtractionTable } from "./stats/ExtractionTable";
import { IndicatorStatsTable } from "./stats/IndicatorStatsTable";
import { ThicknessHistogram } from "./stats/ThicknessHistogram";

export function StatsView() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const requested = searchParams.get("split");
  const split = SPLITS.find((value) => value === requested);
  const { data, error, loading, reload } = useApi(split ?? "all", (signal) =>
    getStats(split, signal),
  );

  function changeSplit(value: string) {
    router.replace(value ? `${pathname}?split=${value}` : pathname);
  }

  const excluded = data?.classes.reduce((sum, item) => sum + item.excluded_duplicates, 0) ?? 0;

  return (
    <>
      <h1>Statistics</h1>
      <form className="filters" onSubmit={(event) => event.preventDefault()} aria-label="Filters">
        <label>
          Split
          <select value={split ?? ""} onChange={(event) => changeSplit(event.target.value)}>
            <option value="">All</option>
            {SPLITS.map((value: Split) => (
              <option key={value} value={value}>
                {SPLIT_TEXT[value]}
              </option>
            ))}
          </select>
        </label>
      </form>
      <Disclaimer />
      {loading && <Loading label="Loading statistics…" />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <>
          <section aria-labelledby="counts-heading" className="panel">
            <h2 id="counts-heading">Exams per class</h2>
            <ClassCountChart classes={data.classes} />
            <p className="muted">
              {excluded} {excluded === 1 ? "exam" : "exams"} excluded as possible duplicates
              {excluded > 0 &&
                ` (${data.classes.map((item) => `${LABEL_TEXT[item.label]}: ${item.excluded_duplicates}`).join(", ")})`}
              . <Link href="/">Browse the exam list</Link>.
            </p>
          </section>
          <section aria-labelledby="thickness-heading" className="panel">
            <h2 id="thickness-heading">Visible minimum thickness</h2>
            <ThicknessHistogram classes={data.classes} />
          </section>
          <section aria-labelledby="indicators-stats-heading" className="panel">
            <h2 id="indicators-stats-heading">Indicators per class</h2>
            <IndicatorStatsTable classes={data.classes} />
          </section>
          <section aria-labelledby="extraction-heading" className="panel">
            <h2 id="extraction-heading">Extraction quality</h2>
            <ExtractionTable classes={data.classes} />
          </section>
        </>
      )}
    </>
  );
}
