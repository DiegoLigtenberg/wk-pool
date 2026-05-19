import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TeamInsightModal } from "./TeamInsightModal";
import type { TeamInsight } from "../../types";

const insight: TeamInsight = {
  team: "Bosnië-Herzegovina",
  tier: "Verrassingsploeg",
  style: "technisch in fases",
  powerScore: 65,
  strengths: ["ervaring"],
  risks: ["tempo"],
  group: "B",
  opponents: ["Canada", "Qatar", "Zwitserland"],
  groupContext: [
    "Wedstrijd 1: uit tegen Canada (Toronto Stadium)",
    "Wedstrijd 2: uit tegen Zwitserland (Los Angeles Stadium)",
    "Wedstrijd 3: thuis tegen Qatar (Seattle Stadium)",
  ],
  summary: "Test",
};

describe("TeamInsightModal", () => {
  it("shows group and fixtures in one block without duplicating opponent list", () => {
    render(<TeamInsightModal insight={insight} onClose={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Groep B" })).toBeInTheDocument();
    expect(screen.getByText(/uit tegen Canada/)).toBeInTheDocument();
    expect(screen.queryByText("Groep B: Canada, Qatar, Zwitserland")).not.toBeInTheDocument();
    expect(screen.queryByText("Groepsprogramma")).not.toBeInTheDocument();
  });
});
