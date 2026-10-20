import {
  LABELS,
  LATERALITIES,
  SPLITS,
  type ExamQuery,
  type Label,
  type Laterality,
  type SortKey,
  type SortOrder,
  type Split,
} from "./types";

function oneOf<T extends string>(allowed: readonly T[], value: string | null): T | undefined {
  return allowed.find((item) => item === value);
}

export function parseExamQuery(params: URLSearchParams): ExamQuery {
  const page = Number.parseInt(params.get("page") ?? "1", 10);
  return {
    split: oneOf<Split>(SPLITS, params.get("split")),
    label: oneOf<Label>(LABELS, params.get("label")),
    laterality: oneOf<Laterality>(LATERALITIES, params.get("laterality")),
    page: Number.isFinite(page) && page >= 1 ? page : 1,
    sort: oneOf<SortKey>(["case", "min_thickness"], params.get("sort")) ?? "case",
    order: oneOf<SortOrder>(["asc", "desc"], params.get("order")) ?? "asc",
  };
}

/** Serialises the query for the browser URL; defaults are left out to keep URLs short. */
export function serialiseExamQuery(query: ExamQuery): string {
  const params = new URLSearchParams();
  if (query.split) params.set("split", query.split);
  if (query.label) params.set("label", query.label);
  if (query.laterality) params.set("laterality", query.laterality);
  if (query.sort !== "case") params.set("sort", query.sort);
  if (query.order !== "asc") params.set("order", query.order);
  if (query.page !== 1) params.set("page", String(query.page));
  return params.toString();
}
