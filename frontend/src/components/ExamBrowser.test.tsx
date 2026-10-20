import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { makePage, makeSummary } from "@/test/fixtures";
import { ExamBrowser } from "./ExamBrowser";

const replace = vi.fn();
let search = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(search),
}));

const listExams = vi.fn();
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  listExams: (...args: unknown[]) => listExams(...args),
}));

beforeEach(() => {
  search = "";
  replace.mockClear();
  listExams.mockReset();
});

describe("ExamBrowser", () => {
  it("shows a loading state and then the exams", async () => {
    listExams.mockResolvedValue(
      makePage([makeSummary(), makeSummary({ exam_id: "train_validation/normal/2", case: 2 })]),
    );
    render(<ExamBrowser />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading exams");
    expect(await screen.findAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("2 exams")).toBeInTheDocument();
  });

  it("shows the card facts, with dashes for missing values", async () => {
    listExams.mockResolvedValue(
      makePage([
        makeSummary({ min_thickness_um: null, max_curvature_a_d: null, laterality: "unknown" }),
      ]),
    );
    render(<ExamBrowser />);
    const card = await screen.findByRole("listitem");
    expect(within(card).getByText("Laterality unknown")).toBeInTheDocument();
    expect(within(card).getAllByText("—")).toHaveLength(2);
  });

  it("marks possible duplicates", async () => {
    listExams.mockResolvedValue(
      makePage([makeSummary({ possible_duplicate_of: ["train_validation/normal/9"] })]),
    );
    render(<ExamBrowser />);
    expect(await screen.findByText("Possible duplicate")).toBeInTheDocument();
  });

  it("shows an empty state", async () => {
    listExams.mockResolvedValue(makePage([]));
    render(<ExamBrowser />);
    expect(await screen.findByText("No exams match the filters")).toBeInTheDocument();
  });

  it("shows the server message and retries on error", async () => {
    listExams
      .mockRejectedValueOnce(new ApiError(503, "Exam index not available. Run the ingestion."))
      .mockResolvedValueOnce(makePage([makeSummary()]));
    render(<ExamBrowser />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Exam index not available");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("listitem")).toBeInTheDocument();
    expect(listExams).toHaveBeenCalledTimes(2);
  });

  it("reads the filters from the URL and passes them to the API", async () => {
    search = "label=suspect&laterality=OS&sort=min_thickness&order=desc&page=2";
    listExams.mockResolvedValue(makePage([makeSummary()], { page: 2, total: 40 }));
    render(<ExamBrowser />);
    await screen.findByRole("listitem");
    expect(listExams.mock.calls[0][0]).toMatchObject({
      label: "suspect",
      laterality: "OS",
      sort: "min_thickness",
      order: "desc",
      page: 2,
    });
    expect(screen.getByLabelText("Dataset label")).toHaveValue("suspect");
    expect(screen.getByLabelText("Sort by")).toHaveValue("min_thickness:desc");
  });

  it("writes a filter change to the URL and goes back to page 1", async () => {
    search = "page=3";
    listExams.mockResolvedValue(makePage([makeSummary()], { page: 3, total: 100 }));
    render(<ExamBrowser />);
    await screen.findByRole("listitem");
    await userEvent.selectOptions(screen.getByLabelText("Dataset label"), "keratoconus");
    expect(replace).toHaveBeenCalledWith("/?label=keratoconus");
  });

  it("clears the URL when the last filter is removed", async () => {
    search = "label=normal";
    listExams.mockResolvedValue(makePage([makeSummary()]));
    render(<ExamBrowser />);
    await screen.findByRole("listitem");
    await userEvent.selectOptions(screen.getByLabelText("Dataset label"), "");
    expect(replace).toHaveBeenCalledWith("/");
  });

  it("changes the sort", async () => {
    listExams.mockResolvedValue(makePage([makeSummary()]));
    render(<ExamBrowser />);
    await screen.findByRole("listitem");
    await userEvent.selectOptions(screen.getByLabelText("Sort by"), "min_thickness:asc");
    expect(replace).toHaveBeenCalledWith("/?sort=min_thickness");
  });

  it("paginates", async () => {
    listExams.mockResolvedValue(makePage([makeSummary()], { total: 573, page: 1 }));
    render(<ExamBrowser />);
    await screen.findByRole("listitem");
    expect(screen.getByText("Page 1 of 24")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(replace).toHaveBeenCalledWith("/?page=2");
  });

  it("disables Next on the last page", async () => {
    search = "page=24";
    listExams.mockResolvedValue(makePage([makeSummary()], { total: 573, page: 24 }));
    render(<ExamBrowser />);
    await waitFor(() => expect(screen.getByText("Page 24 of 24")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("links cards to the detail page and keeps the filters for the way back", async () => {
    search = "label=normal";
    listExams.mockResolvedValue(makePage([makeSummary()]));
    render(<ExamBrowser />);
    const link = await screen.findByRole("link");
    expect(link).toHaveAttribute("href", "/exams/train_validation/normal/1?label=normal");
  });
});
