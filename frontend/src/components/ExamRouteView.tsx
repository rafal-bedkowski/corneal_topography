"use client";

import { useParams } from "next/navigation";
import { ExamDetailView } from "./ExamDetailView";

export function ExamRouteView() {
  const {
    split,
    label,
    case: caseNumber,
  } = useParams<{ split: string; label: string; case: string }>();
  return <ExamDetailView split={split} label={label} caseNumber={caseNumber} />;
}
