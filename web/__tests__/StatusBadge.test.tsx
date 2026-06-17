import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusBadge } from "../components/StatusBadge";

describe("StatusBadge", () => {
  it("renders 'Found' label for found status", () => {
    render(<StatusBadge status="found" />);
    expect(screen.getByText("Found")).toBeInTheDocument();
  });

  it("renders 'Submitted' label for submitted status", () => {
    render(<StatusBadge status="submitted" />);
    expect(screen.getByText("Submitted")).toBeInTheDocument();
  });

  it("renders 'Cleared' label for cleared status", () => {
    render(<StatusBadge status="cleared" />);
    expect(screen.getByText("Cleared")).toBeInTheDocument();
  });

  it("renders 'Manual Required' for manual_required", () => {
    render(<StatusBadge status="manual_required" />);
    expect(screen.getByText("Manual Required")).toBeInTheDocument();
  });

  it("renders 'Pending Verification' for pending_verification", () => {
    render(<StatusBadge status="pending_verification" />);
    expect(screen.getByText("Pending Verification")).toBeInTheDocument();
  });

  it("renders 'Not Found' for not_found", () => {
    render(<StatusBadge status="not_found" />);
    expect(screen.getByText("Not Found")).toBeInTheDocument();
  });

  it("applies danger colour class for found status", () => {
    const { container } = render(<StatusBadge status="found" />);
    expect(container.firstChild).toHaveClass("bg-red-900");
  });

  it("applies success colour class for cleared status", () => {
    const { container } = render(<StatusBadge status="cleared" />);
    expect(container.firstChild).toHaveClass("bg-green-900");
  });
});
