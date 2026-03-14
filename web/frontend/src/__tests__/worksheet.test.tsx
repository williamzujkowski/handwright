import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock api module
vi.mock("@/lib/api", () => ({
  generateWorksheet: vi.fn(),
}));

import WorksheetPage from "../app/worksheet/page";

describe("WorksheetPage", () => {
  it("renders the page heading", () => {
    render(<WorksheetPage />);
    const headings = screen.getAllByText("Generate Worksheet");
    expect(headings.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the generate button", () => {
    render(<WorksheetPage />);
    const buttons = screen.getAllByRole("button");
    const genButton = buttons.find(
      (b) => b.textContent === "Generate & Download Worksheet",
    );
    expect(genButton).toBeDefined();
  });

  it("renders the include symbols checkbox", () => {
    render(<WorksheetPage />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThanOrEqual(1);
  });

  it("renders instructions", () => {
    render(<WorksheetPage />);
    const items = screen.getAllByText(/Print the PDF on standard letter/);
    expect(items.length).toBeGreaterThanOrEqual(1);
  });

  it("has a link to the upload page", () => {
    render(<WorksheetPage />);
    const links = screen.getAllByRole("link");
    const uploadLink = links.find(
      (el) => el.getAttribute("href") === "/upload",
    );
    expect(uploadLink).toBeDefined();
  });
});
