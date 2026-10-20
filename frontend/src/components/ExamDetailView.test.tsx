import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { DISCLAIMER } from "@/lib/format";
import { makeDetail, makeValue } from "@/test/fixtures";
import { ExamDetailView } from "./ExamDetailView";

let search = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(search),
}));

const getExam = vi.fn();
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getExam: (...args: unknown[]) => getExam(...args),
}));

function renderView() {
  return render(<ExamDetailView split="train_validation" label="normal" caseNumber="1" />);
}

beforeEach(() => {
  search = "";
  getExam.mockReset();
});

describe("ExamDetailView", () => {
  it("shows a loading state", () => {
    getExam.mockReturnValue(new Promise(() => undefined));
    renderView();
    expect(screen.getByRole("status")).toHaveTextContent("Loading exam");
  });

  it("shows the header, notice, indicators and seven maps", async () => {
    getExam.mockResolvedValue(makeDetail());
    renderView();
    expect(await screen.findByRole("heading", { name: "Exam 1" })).toBeInTheDocument();
    expect(screen.getByText("Dataset label: Normal")).toBeInTheDocument();
    expect(screen.getByText("Right eye (OD)")).toBeInTheDocument();
    expect(screen.getByText("Train / validation")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(DISCLAIMER);
    expect(screen.getAllByRole("figure")).toHaveLength(7);
    const panel = screen.getByRole("heading", { name: /Indicators/ }).closest("section");
    for (const text of ["558 µm", "42.4 D", "40.7 D", "1.7 D", "2 µm", "8 µm"]) {
      expect(within(panel as HTMLElement).getByText(text)).toBeInTheDocument();
    }
  });

  it("makes no diagnostic claim", async () => {
    getExam.mockResolvedValue(makeDetail({ label: "keratoconus" }));
    renderView();
    await screen.findByRole("heading", { name: "Exam 1" });
    expect(screen.getByText("Dataset label: Keratoconus")).toBeInTheDocument();
    expect(screen.queryByText(/diagnos(is|ed)/i)).not.toBeInTheDocument();
  });

  it("shows dashes for indicators without a value", async () => {
    const detail = makeDetail();
    detail.indicators = {
      min_thickness_um: null,
      max_curvature_a_d: null,
      min_curvature_a_d: null,
      curvature_spread_a_d: null,
      max_elevation_a_um: null,
      max_elevation_p_um: null,
    };
    getExam.mockResolvedValue(detail);
    renderView();
    const panel = (await screen.findByRole("heading", { name: /Indicators/ })).closest("section");
    expect(within(panel as HTMLElement).getAllByText("—")).toHaveLength(6);
  });

  it("shows a duplicate notice with links and the exclusion reason", async () => {
    getExam.mockResolvedValue(
      makeDetail({
        possible_duplicate_of: ["independent_test/suspect/7"],
        stats_excluded: true,
        stats_exclusion_reason: "duplicate_conflicting_labels",
      }),
    );
    renderView();
    const link = await screen.findByRole("link", { name: /suspect · case 7/ });
    expect(link).toHaveAttribute("href", "/exams/independent_test/suspect/7");
    expect(screen.getByText(/labels of the duplicates disagree/)).toBeInTheDocument();
  });

  it("says when a duplicate is still counted in the statistics", async () => {
    getExam.mockResolvedValue(makeDetail({ possible_duplicate_of: ["train_validation/normal/9"] }));
    renderView();
    expect(await screen.findByText("It is included in the statistics.")).toBeInTheDocument();
  });

  it("lists accepted values first, then flagged ones, and hides ignored labels by default", async () => {
    const detail = makeDetail();
    detail.maps.ct_a!.values = [
      makeValue({ text: "4000", value: null, status: "out_of_range" }),
      makeValue({ text: "90°", value: null, status: "rejected" }),
      makeValue({ text: "558", value: 558 }),
      makeValue({ text: "476", value: 476, confidence: 0.4, status: "low_confidence" }),
    ];
    getExam.mockResolvedValue(detail);
    renderView();
    const figure = (await screen.findByText("Map ct_a")).closest("figure") as HTMLElement;
    const rows = within(figure).getAllByRole("row").slice(1);
    expect(rows.map((row) => within(row).getAllByRole("cell")[0].textContent)).toEqual([
      "558",
      "4000",
      "476",
    ]);
    expect(
      within(figure).getByText("Extracted values (1 accepted, 2 flagged)"),
    ).toBeInTheDocument();
    await userEvent.click(within(figure).getByLabelText(/Show 1 ignored labels/));
    expect(within(figure).getByText("90°")).toBeInTheDocument();
  });

  it("says when a map has no values", async () => {
    const detail = makeDetail();
    detail.maps.ct_a!.values = [];
    getExam.mockResolvedValue(detail);
    renderView();
    expect(await screen.findByText("No values were extracted from this map.")).toBeInTheDocument();
  });

  it("enlarges a map and closes it with Escape", async () => {
    getExam.mockResolvedValue(makeDetail());
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: "Enlarge Map ct_a" }));
    const dialog = screen.getByRole("dialog", { name: "Map ct_a" });
    expect(dialog).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes the enlarged map with the Close button", async () => {
    getExam.mockResolvedValue(makeDetail());
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: "Enlarge Map ct_a" }));
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows 'Exam not found' for a 404", async () => {
    getExam.mockRejectedValue(new ApiError(404, "Exam not found"));
    renderView();
    expect(await screen.findByText("Exam not found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to exams/ })).toHaveAttribute("href", "/");
  });

  it("shows other errors with a retry", async () => {
    getExam
      .mockRejectedValueOnce(new ApiError(503, "Index missing"))
      .mockResolvedValueOnce(makeDetail());
    renderView();
    expect(await screen.findByRole("alert")).toHaveTextContent("Index missing");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("heading", { name: "Exam 1" })).toBeInTheDocument();
  });

  it("links back to the list with the filters that were active", async () => {
    search = "label=normal&page=2";
    getExam.mockResolvedValue(makeDetail());
    renderView();
    expect(await screen.findByRole("link", { name: /Back to exams/ })).toHaveAttribute(
      "href",
      "/?label=normal&page=2",
    );
  });
});
