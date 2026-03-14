import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock api module
vi.mock("@/lib/api", () => ({
  uploadImage: vi.fn(),
}));

import UploadPage from "../app/upload/page";

describe("UploadPage", () => {
  it("renders the page heading", () => {
    render(<UploadPage />);
    const headings = screen.getAllByText("Upload Handwriting");
    expect(headings.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the drag-and-drop zone", () => {
    render(<UploadPage />);
    const zones = screen.getAllByLabelText("Upload worksheet image");
    expect(zones.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the Choose File button", () => {
    render(<UploadPage />);
    const buttons = screen.getAllByText("Choose File");
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it("shows error for unsupported file format", async () => {
    render(<UploadPage />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const file = new File(["content"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    const errors = await screen.findAllByText(/Unsupported format/);
    expect(errors.length).toBeGreaterThanOrEqual(1);
  });

  it("shows error for oversized files", async () => {
    render(<UploadPage />);

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const largeContent = new ArrayBuffer(11 * 1024 * 1024);
    const file = new File([largeContent], "large.png", { type: "image/png" });

    fireEvent.change(input, { target: { files: [file] } });

    const errors = await screen.findAllByText(/maximum is 10 MB/);
    expect(errors.length).toBeGreaterThanOrEqual(1);
  });

  it("displays the max file size note", () => {
    render(<UploadPage />);
    const notes = screen.getAllByText(/Maximum file size: 10 MB/);
    expect(notes.length).toBeGreaterThanOrEqual(1);
  });
});
