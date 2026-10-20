export const SPLITS = ["train_validation", "independent_test"] as const;
export const LABELS = ["normal", "keratoconus", "suspect"] as const;
export const LATERALITIES = ["OD", "OS", "unknown"] as const;
export const MAP_TYPES = ["sag_a", "sag_p", "elv_a", "elv_p", "ec_a", "ec_p", "ct_a"] as const;

export type Split = (typeof SPLITS)[number];
export type Label = (typeof LABELS)[number];
export type Laterality = (typeof LATERALITIES)[number];
export type MapType = (typeof MAP_TYPES)[number];
export type ValueStatus = "accepted" | "low_confidence" | "out_of_range" | "rejected";
export type ExclusionReason = "duplicate" | "duplicate_conflicting_labels";

export interface ExtractedValue {
  text: string;
  value: number | null;
  confidence: number;
  x: number;
  y: number;
  status: ValueStatus;
}

export interface Indicators {
  min_thickness_um: number | null;
  max_curvature_a_d: number | null;
  min_curvature_a_d: number | null;
  curvature_spread_a_d: number | null;
  max_elevation_a_um: number | null;
  max_elevation_p_um: number | null;
}

export type IndicatorKey = keyof Indicators;

export interface ExamSummary {
  exam_id: string;
  split: Split;
  label: Label;
  case: number;
  laterality: Laterality;
  min_thickness_um: number | null;
  max_curvature_a_d: number | null;
  possible_duplicate_of: string[];
  stats_excluded: boolean;
  thumbnail_url: string | null;
}

export interface ExamPage {
  total: number;
  page: number;
  page_size: number;
  items: ExamSummary[];
}

export interface MapDetail {
  title: string;
  unit: string;
  image_url: string;
  values: ExtractedValue[];
}

export interface ExamDetail {
  exam_id: string;
  split: Split;
  label: Label;
  case: number;
  laterality: Laterality;
  maps: Partial<Record<MapType, MapDetail>>;
  indicators: Indicators;
  possible_duplicate_of: string[];
  stats_excluded: boolean;
  stats_exclusion_reason: ExclusionReason | null;
}

export interface SummaryStats {
  n: number;
  mean: number | null;
  median: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
}

export interface HistogramBin {
  from: number;
  count: number;
}

export interface Histogram {
  bin_width: number;
  bins: HistogramBin[];
}

export interface ExtractionCounts {
  accepted: number;
  low_confidence: number;
  out_of_range: number;
  rejected: number;
}

export interface ClassStats {
  label: Label;
  exams: number;
  excluded_duplicates: number;
  laterality: Record<Laterality, number>;
  indicators: Record<IndicatorKey, SummaryStats>;
  histograms: Record<"min_thickness_um", Histogram>;
  extraction: ExtractionCounts;
}

export interface StatsResponse {
  classes: ClassStats[];
}

export type SortKey = "case" | "min_thickness";
export type SortOrder = "asc" | "desc";

export interface ExamQuery {
  split?: Split;
  label?: Label;
  laterality?: Laterality;
  page: number;
  sort: SortKey;
  order: SortOrder;
}
