import { describe, expect, it } from "vitest";
import { parseExamQuery, serialiseExamQuery } from "./examQuery";

describe("parseExamQuery", () => {
  it("falls back to defaults", () => {
    expect(parseExamQuery(new URLSearchParams())).toEqual({
      split: undefined,
      label: undefined,
      laterality: undefined,
      page: 1,
      sort: "case",
      order: "asc",
    });
  });

  it("reads valid values", () => {
    const query = parseExamQuery(
      new URLSearchParams(
        "split=independent_test&label=suspect&laterality=OS&sort=min_thickness&order=desc&page=3",
      ),
    );
    expect(query).toEqual({
      split: "independent_test",
      label: "suspect",
      laterality: "OS",
      page: 3,
      sort: "min_thickness",
      order: "desc",
    });
  });

  it("ignores invalid values", () => {
    const query = parseExamQuery(
      new URLSearchParams("split=nope&label=x&laterality=left&sort=y&order=up&page=-2"),
    );
    expect(query.split).toBeUndefined();
    expect(query.label).toBeUndefined();
    expect(query.laterality).toBeUndefined();
    expect(query.sort).toBe("case");
    expect(query.order).toBe("asc");
    expect(query.page).toBe(1);
  });

  it("treats a non-numeric page as 1", () => {
    expect(parseExamQuery(new URLSearchParams("page=abc")).page).toBe(1);
  });
});

describe("serialiseExamQuery", () => {
  it("omits defaults", () => {
    expect(serialiseExamQuery({ page: 1, sort: "case", order: "asc" })).toBe("");
  });

  it("round-trips a full query", () => {
    const query = parseExamQuery(
      new URLSearchParams(
        "split=train_validation&label=normal&laterality=unknown&sort=min_thickness&order=desc&page=2",
      ),
    );
    expect(parseExamQuery(new URLSearchParams(serialiseExamQuery(query)))).toEqual(query);
  });
});
