import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FindingsTable } from "../components/FindingsTable";
import type { Finding } from "../lib/types";

const FINDINGS: Finding[] = [
  {
    id: 1,
    user_display_name: "Alice",
    source: "brokers",
    site_id: "whitepages",
    site_name: "Whitepages",
    status: "found",
    opt_out_url: "https://whitepages.com/opt-out",
    listing_url: "https://www.whitepages.com/name/Alice+Test/Portland-OR",
    manual_instructions: null,
    last_checked: "2026-06-17T10:00:00",
    submitted_at: null,
  },
  {
    id: 2,
    user_display_name: "Alice",
    source: "brokers",
    site_id: "spokeo",
    site_name: "Spokeo",
    status: "cleared",
    opt_out_url: "https://spokeo.com/opt-out",
    listing_url: null,
    manual_instructions: null,
    last_checked: "2026-06-17T10:00:00",
    submitted_at: "2026-06-17T10:05:00",
  },
];

describe("FindingsTable", () => {
  it("renders site names", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    expect(screen.getByText("Whitepages")).toBeInTheDocument();
    expect(screen.getByText("Spokeo")).toBeInTheDocument();
  });

  it("renders detection badges", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    expect(screen.getAllByText("Exposed").length).toBeGreaterThan(0);
    expect(screen.getByText("Cleared ✓")).toBeInTheDocument();
  });

  it("renders listing and opt-out links", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    const links = screen.getAllByRole("link");
    expect(links.some((l) => l.getAttribute("href")?.includes("whitepages"))).toBe(true);
    expect(screen.getByText("View Listing ↗")).toBeInTheDocument();
  });

  it("calls onStatusChange when Mark Cleared button clicked", () => {
    const onStatusChange = vi.fn();
    render(<FindingsTable findings={FINDINGS} onStatusChange={onStatusChange} />);
    const clearBtn = screen.getByText("Mark Cleared");
    fireEvent.click(clearBtn);
    expect(onStatusChange).toHaveBeenCalledWith(1, "cleared");
  });

  it("shows empty state message when no findings", () => {
    render(<FindingsTable findings={[]} onStatusChange={vi.fn()} />);
    expect(screen.getByText(/no findings/i)).toBeInTheDocument();
  });
});
