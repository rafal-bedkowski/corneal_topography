import {
  LABELS,
  MAP_TYPES,
  type ClassStats,
  type ExamDetail,
  type ExamPage,
  type ExamSummary,
  type ExtractedValue,
  type Label,
  type MapDetail,
  type StatsResponse,
} from "@/lib/types";

export function makeSummary(overrides: Partial<ExamSummary> = {}): ExamSummary {
  return {
    exam_id: "train_validation/normal/1",
    split: "train_validation",
    label: "normal",
    case: 1,
    laterality: "OD",
    min_thickness_um: 558,
    max_curvature_a_d: 42.4,
    possible_duplicate_of: [],
    stats_excluded: false,
    thumbnail_url: "/api/exams/train_validation/normal/1/maps/sag_a/image",
    ...overrides,
  };
}

export function makePage(items: ExamSummary[], overrides: Partial<ExamPage> = {}): ExamPage {
  return { total: items.length, page: 1, page_size: 24, items, ...overrides };
}

export function makeValue(overrides: Partial<ExtractedValue> = {}): ExtractedValue {
  return {
    text: "558",
    value: 558,
    confidence: 1,
    x: 0.5,
    y: 0.5,
    status: "accepted",
    ...overrides,
  };
}

export function makeDetail(overrides: Partial<ExamDetail> = {}): ExamDetail {
  const maps: ExamDetail["maps"] = {};
  for (const type of MAP_TYPES) {
    const map: MapDetail = {
      title: `Map ${type}`,
      unit: type === "ct_a" || type.startsWith("e") ? "µm" : "D",
      image_url: `/api/exams/train_validation/normal/1/maps/${type}/image`,
      values: [makeValue()],
    };
    maps[type] = map;
  }
  return {
    exam_id: "train_validation/normal/1",
    split: "train_validation",
    label: "normal",
    case: 1,
    laterality: "OD",
    maps,
    indicators: {
      min_thickness_um: 558,
      max_curvature_a_d: 42.4,
      min_curvature_a_d: 40.7,
      curvature_spread_a_d: 1.7,
      max_elevation_a_um: 2,
      max_elevation_p_um: 8,
    },
    possible_duplicate_of: [],
    stats_excluded: false,
    stats_exclusion_reason: null,
    ...overrides,
  };
}

function makeClass(label: Label, exams: number, excluded: number, from: number): ClassStats {
  const stat = { n: exams, mean: 500.123, median: 500, std: 12.5, min: 480, max: 520 };
  return {
    label,
    exams,
    excluded_duplicates: excluded,
    laterality: { OD: 1, OS: 1, unknown: 0 },
    indicators: {
      min_thickness_um: stat,
      max_curvature_a_d: stat,
      min_curvature_a_d: stat,
      curvature_spread_a_d: stat,
      max_elevation_a_um: stat,
      max_elevation_p_um: stat,
    },
    histograms: {
      min_thickness_um: {
        bin_width: 20,
        bins: [
          { from, count: 2 },
          { from: from + 20, count: 1 },
        ],
      },
    },
    extraction: { accepted: 10, low_confidence: 2, out_of_range: 3, rejected: 4 },
  };
}

export function makeStats(): StatsResponse {
  return {
    classes: LABELS.map((label, index) => makeClass(label, 100 + index, index, 460 + index * 20)),
  };
}
