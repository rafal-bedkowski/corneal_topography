import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { DISCLAIMER } from "@/lib/format";
import { makeStats } from "@/test/fixtures";
import { mergeHistograms } from "./stats/ThicknessHistogram";
import { StatsView } from "./StatsView";

const replace = vi.fn();
let search = "";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/stats",
  useSearchParams: () => new URLSearchParams(search),
}));

const getStats = vi.fn();
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getStats: (...args: unknown[]) => getStats(...args),
}));

// Recharts needs real layout; the charts are covered by their data helpers and aria labels.
vi.mock("recharts", () => {
  const Passthrough = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
  return {
    ResponsiveContainer: Passthrough,
    BarChart: Passthrough,
    Bar: Passthrough,
    Cell: () => null,
    CartesianGrid: () => null,
    XAxis: () => null,
    YAxis: () => null,
    Tooltip: () => null,
    Legend: () => null,
  };
});

beforeEach(() => {
  search = "";
  replace.mockClear();
  getStats.mockReset();
});

describe("StatsView", () => {
  it("shows a loading state", () => {
    getStats.mockReturnValue(new Promise(() => undefined));
    render(<StatsView />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading statistics");
  });

  it("shows the notice, the class chart summary and the excluded duplicates", async () => {
    getStats.mockResolvedValue(makeStats());
    render(<StatsView />);
    expect(
      await screen.findByRole("img", {
        name: "Exams per class: Normal 100, Keratoconus 101, Suspect 102",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(DISCLAIMER);
    expect(
      screen.getByText(
        /3 exams excluded as possible duplicates \(Normal: 0, Keratoconus: 1, Suspect: 2\)/,
      ),
    ).toBeInTheDocument();
  });

  it("does not list per-class exclusions when none were excluded", async () => {
    const stats = makeStats();
    for (const item of stats.classes) item.excluded_duplicates = 0;
    getStats.mockResolvedValue(stats);
    render(<StatsView />);
    expect(
      await screen.findByText(/0 exams excluded as possible duplicates\./),
    ).toBeInTheDocument();
  });

  it("renders the indicator table with one row per class and indicator", async () => {
    getStats.mockResolvedValue(makeStats());
    render(<StatsView />);
    const table = (await screen.findByRole("table", {
      name: /Indicator statistics/,
    })) as HTMLElement;
    expect(within(table).getAllByRole("row")).toHaveLength(1 + 6 * 3);
    expect(within(table).getAllByText("500.1").length).toBeGreaterThan(0);
    expect(within(table).getAllByText("12.5").length).toBeGreaterThan(0);
  });

  it("renders the extraction quality table", async () => {
    getStats.mockResolvedValue(makeStats());
    render(<StatsView />);
    const table = await screen.findByRole("table", { name: /text extraction/ });
    const normal = within(table).getByRole("row", { name: /Normal/ });
    expect(
      within(normal)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["10", "2", "3", "4"]);
  });

  it("shows dashes where a statistic is undefined", async () => {
    const stats = makeStats();
    stats.classes[0].indicators.min_thickness_um = {
      n: 1,
      mean: 500,
      median: 500,
      std: null,
      min: 500,
      max: 500,
    };
    getStats.mockResolvedValue(stats);
    render(<StatsView />);
    const table = (await screen.findByRole("table", {
      name: /Indicator statistics/,
    })) as HTMLElement;
    expect(within(table).getAllByText("—").length).toBeGreaterThan(0);
  });

  it("requests the split from the URL and writes a change back", async () => {
    search = "split=independent_test";
    getStats.mockResolvedValue(makeStats());
    render(<StatsView />);
    await screen.findByRole("note");
    expect(getStats.mock.calls[0][0]).toBe("independent_test");
    expect(screen.getByLabelText("Split")).toHaveValue("independent_test");
    await userEvent.selectOptions(screen.getByLabelText("Split"), "train_validation");
    expect(replace).toHaveBeenCalledWith("/stats?split=train_validation");
    await userEvent.selectOptions(screen.getByLabelText("Split"), "");
    expect(replace).toHaveBeenCalledWith("/stats");
  });

  it("shows errors with a retry", async () => {
    getStats
      .mockRejectedValueOnce(new ApiError(503, "Index missing"))
      .mockResolvedValueOnce(makeStats());
    render(<StatsView />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Index missing");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("img", { name: /Exams per class/ })).toBeInTheDocument();
  });
});

describe("mergeHistograms", () => {
  it("joins the bins of all classes on one axis", () => {
    const { rows, binWidth } = mergeHistograms(makeStats().classes);
    expect(binWidth).toBe(20);
    expect(rows.map((row) => row.from)).toEqual([460, 480, 500, 520]);
    expect(rows[0]).toMatchObject({ range: "460–479", normal: 2 });
    expect(rows[0].keratoconus).toBeUndefined();
    expect(rows[2]).toMatchObject({ keratoconus: 1, suspect: 2 });
    expect(rows[2].normal).toBeUndefined();
  });

  it("is empty without data", () => {
    const stats = makeStats();
    for (const item of stats.classes) item.histograms.min_thickness_um.bins = [];
    expect(mergeHistograms(stats.classes).rows).toEqual([]);
  });
});
