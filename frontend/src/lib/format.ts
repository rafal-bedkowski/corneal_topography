import type { ExclusionReason, IndicatorKey, Label, Laterality, Split, ValueStatus } from "./types";

export const LABEL_TEXT: Record<Label, string> = {
  normal: "Normal",
  keratoconus: "Keratoconus",
  suspect: "Suspect",
};

export const SPLIT_TEXT: Record<Split, string> = {
  train_validation: "Train / validation",
  independent_test: "Independent test",
};

export const LATERALITY_TEXT: Record<Laterality, string> = {
  OD: "Right eye (OD)",
  OS: "Left eye (OS)",
  unknown: "Laterality unknown",
};

export const STATUS_TEXT: Record<ValueStatus, string> = {
  accepted: "Accepted",
  low_confidence: "Low confidence",
  out_of_range: "Out of range",
  rejected: "Ignored label",
};

export const EXCLUSION_TEXT: Record<ExclusionReason, string> = {
  duplicate: "Excluded from the statistics as a duplicate of another exam.",
  duplicate_conflicting_labels:
    "Excluded from the statistics: the labels of the duplicates disagree.",
};

export const INDICATOR_TEXT: Record<IndicatorKey, { name: string; unit: string }> = {
  min_thickness_um: { name: "Visible min thickness", unit: "µm" },
  max_curvature_a_d: { name: "Visible max curvature (anterior)", unit: "D" },
  min_curvature_a_d: { name: "Visible min curvature (anterior)", unit: "D" },
  curvature_spread_a_d: { name: "Visible curvature spread (anterior)", unit: "D" },
  max_elevation_a_um: { name: "Visible max elevation (anterior)", unit: "µm" },
  max_elevation_p_um: { name: "Visible max elevation (posterior)", unit: "µm" },
};

export const INDICATOR_KEYS = Object.keys(INDICATOR_TEXT) as IndicatorKey[];

export const INDICATOR_TOOLTIP =
  "Derived from values printed on the map image by automatic text recognition. " +
  "Not a clinical measurement.";

export const DISCLAIMER =
  "Values are extracted automatically from images and may contain errors. " +
  "For research and demonstration only; not a clinical tool.";

export function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

export function formatIndicator(key: IndicatorKey, value: number | null): string {
  if (value === null) return "—";
  const { unit } = INDICATOR_TEXT[key];
  const digits = unit === "D" ? 1 : 0;
  return `${value.toFixed(digits)} ${unit}`;
}

export function examPath(examId: string): string {
  return `/exams/${examId.split("/").map(encodeURIComponent).join("/")}`;
}

export function shortExamId(examId: string): string {
  const [split, label, caseNumber] = examId.split("/");
  const prefix = split === "independent_test" ? "test" : "train";
  return `${prefix} · ${label} · case ${caseNumber}`;
}
