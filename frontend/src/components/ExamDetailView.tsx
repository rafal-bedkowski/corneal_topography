"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { getExam } from "@/lib/api";
import { LATERALITY_TEXT, SPLIT_TEXT } from "@/lib/format";
import { MAP_TYPES } from "@/lib/types";
import { DuplicateNotice } from "./DuplicateNotice";
import { IndicatorsPanel } from "./IndicatorsPanel";
import { LabelBadge } from "./LabelBadge";
import { MapPanel } from "./MapPanel";
import { Disclaimer } from "./Notice";
import { EmptyState, ErrorState, Loading } from "./StateViews";

interface Props {
  split: string;
  label: string;
  caseNumber: string;
}

export function ExamDetailView({ split, label, caseNumber }: Props) {
  const searchParams = useSearchParams();
  const back = searchParams.toString();
  const key = `${split}/${label}/${caseNumber}`;
  const { data, error, loading, reload } = useApi(key, (signal) =>
    getExam(split, label, caseNumber, signal),
  );

  const backLink = (
    <Link href={back ? `/?${back}` : "/"} className="back">
      ← Back to exams
    </Link>
  );

  if (loading) return <Loading label="Loading exam…" />;
  if (error?.status === 404) {
    return (
      <>
        {backLink}
        <EmptyState message="Exam not found" />
      </>
    );
  }
  if (error) {
    return (
      <>
        {backLink}
        <ErrorState error={error} onRetry={reload} />
      </>
    );
  }
  if (!data) return null;

  return (
    <>
      {backLink}
      <header className="exam-header">
        <h1>Exam {data.case}</h1>
        <div className="exam-header__meta">
          <LabelBadge label={data.label} prefix />
          <span>{LATERALITY_TEXT[data.laterality]}</span>
          <span>{SPLIT_TEXT[data.split]}</span>
        </div>
      </header>
      <Disclaimer />
      <DuplicateNotice
        duplicates={data.possible_duplicate_of}
        excluded={data.stats_excluded}
        reason={data.stats_exclusion_reason}
      />
      <IndicatorsPanel indicators={data.indicators} />
      <section aria-labelledby="maps-heading">
        <h2 id="maps-heading">Maps</h2>
        <div className="maps">
          {MAP_TYPES.map((type) => {
            const map = data.maps[type];
            return map ? <MapPanel key={type} map={map} /> : null;
          })}
        </div>
      </section>
    </>
  );
}
