import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ExamRouteView } from "./ExamRouteView";

vi.mock("next/navigation", () => ({
  useParams: () => ({ split: "independent_test", label: "suspect", case: "7" }),
  useSearchParams: () => new URLSearchParams(),
}));

const getExam = vi.fn();
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getExam: (...args: unknown[]) => getExam(...args),
}));

describe("ExamRouteView", () => {
  it("loads the exam named by the URL segments", async () => {
    getExam.mockReturnValue(new Promise(() => undefined));
    render(<ExamRouteView />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading exam");
    expect(getExam).toHaveBeenCalledWith("independent_test", "suspect", "7", expect.anything());
  });
});
