import { LABEL_TEXT, LATERALITY_TEXT, SPLIT_TEXT } from "@/lib/format";
import {
  LABELS,
  LATERALITIES,
  SPLITS,
  type ExamQuery,
  type Label,
  type Laterality,
  type Split,
} from "@/lib/types";

const SORT_OPTIONS: { value: string; text: string }[] = [
  { value: "case:asc", text: "Case number, ascending" },
  { value: "case:desc", text: "Case number, descending" },
  { value: "min_thickness:asc", text: "Visible min thickness, thinnest first" },
  { value: "min_thickness:desc", text: "Visible min thickness, thickest first" },
];

interface Props {
  query: ExamQuery;
  onChange: (patch: Partial<ExamQuery>) => void;
}

export function ExamFilters({ query, onChange }: Props) {
  return (
    <form className="filters" onSubmit={(event) => event.preventDefault()} aria-label="Filters">
      <label>
        Split
        <select
          value={query.split ?? ""}
          onChange={(event) =>
            onChange({ split: (event.target.value || undefined) as Split | undefined })
          }
        >
          <option value="">All</option>
          {SPLITS.map((value) => (
            <option key={value} value={value}>
              {SPLIT_TEXT[value]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Dataset label
        <select
          value={query.label ?? ""}
          onChange={(event) =>
            onChange({ label: (event.target.value || undefined) as Label | undefined })
          }
        >
          <option value="">All</option>
          {LABELS.map((value) => (
            <option key={value} value={value}>
              {LABEL_TEXT[value]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Eye
        <select
          value={query.laterality ?? ""}
          onChange={(event) =>
            onChange({ laterality: (event.target.value || undefined) as Laterality | undefined })
          }
        >
          <option value="">All</option>
          {LATERALITIES.map((value) => (
            <option key={value} value={value}>
              {LATERALITY_TEXT[value]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort by
        <select
          value={`${query.sort}:${query.order}`}
          onChange={(event) => {
            const [sort, order] = event.target.value.split(":");
            onChange({ sort: sort as ExamQuery["sort"], order: order as ExamQuery["order"] });
          }}
        >
          {SORT_OPTIONS.map(({ value, text }) => (
            <option key={value} value={value}>
              {text}
            </option>
          ))}
        </select>
      </label>
    </form>
  );
}
