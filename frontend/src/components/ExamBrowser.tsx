"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { listExams } from "@/lib/api";
import { parseExamQuery, serialiseExamQuery } from "@/lib/examQuery";
import type { ExamQuery } from "@/lib/types";
import { ExamCard } from "./ExamCard";
import { ExamFilters } from "./ExamFilters";
import { Pagination } from "./Pagination";
import { EmptyState, ErrorState, Loading } from "./StateViews";

export function ExamBrowser() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const query = parseExamQuery(searchParams);
  const queryString = serialiseExamQuery(query);
  const { data, error, loading, reload } = useApi(queryString, (signal) =>
    listExams(query, signal),
  );

  function update(patch: Partial<ExamQuery>) {
    const filtersChanged = Object.keys(patch).some((key) => key !== "page");
    const next = { ...query, ...patch, page: filtersChanged ? 1 : (patch.page ?? query.page) };
    const nextString = serialiseExamQuery(next);
    router.replace(nextString ? `${pathname}?${nextString}` : pathname);
  }

  return (
    <>
      <h1>Exams</h1>
      <ExamFilters query={query} onChange={update} />
      {loading && <Loading label="Loading exams…" />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && data.items.length === 0 && <EmptyState message="No exams match the filters" />}
      {data && data.items.length > 0 && (
        <>
          <p className="muted" aria-live="polite">
            {data.total} {data.total === 1 ? "exam" : "exams"}
          </p>
          <ul className="grid">
            {data.items.map((exam) => (
              <ExamCard key={exam.exam_id} exam={exam} backQuery={queryString} />
            ))}
          </ul>
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={(page) => update({ page })}
          />
        </>
      )}
    </>
  );
}
