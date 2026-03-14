import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "../app/page";

describe("HomePage", () => {
  it("renders the main heading", () => {
    render(<HomePage />);
    expect(screen.getByText("Handwright")).toBeInTheDocument();
  });

  it("renders the tagline", () => {
    render(<HomePage />);
    const taglines = screen.getAllByText("Turn your handwriting into a font.");
    expect(taglines.length).toBeGreaterThanOrEqual(1);
  });

  it("renders Get Started link", () => {
    render(<HomePage />);
    const links = screen.getAllByText("Get Started");
    expect(links.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the three how-it-works steps", () => {
    render(<HomePage />);
    expect(screen.getAllByText("Write").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Upload").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Generate").length).toBeGreaterThanOrEqual(1);
  });

  it("renders the footer CTA", () => {
    render(<HomePage />);
    expect(
      screen.getAllByText("Ready to get started?").length,
    ).toBeGreaterThanOrEqual(1);
  });
});
