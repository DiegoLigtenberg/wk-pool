import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { tournamentFixture } from "../../test/tournamentFixture";
import { allMatches } from "../../lib/tournament";
import { MatchesView } from "./MatchesView";

describe("MatchesView", () => {
  it("filters matches and can reveal an AI explanation", async () => {
    const user = userEvent.setup();
    const tournament = tournamentFixture();
    const { container } = render(<MatchesView matches={allMatches(tournament)} summary={tournament.summary} />);

    expect(rows(container)).toHaveLength(2);

    await user.click(screen.getByRole("combobox", { name: "Toon Alle wedstrijden" }));
    await user.click(screen.getByRole("option", { name: "Gespeeld" }));
    expect(rows(container)).toHaveLength(1);
    expect(screen.getByText("2 - 0")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Toon AI-uitleg voor Mexico tegen Zuid-Afrika" }));
    expect(screen.getByText("Mexico wint · 58%")).toBeInTheDocument();

    await user.click(screen.getByRole("combobox", { name: "Fase Alle fases" }));
    await user.click(screen.getByRole("option", { name: "Knock-out" }));

    expect(rows(container)).toHaveLength(0);
    expect(screen.getByText("Geen wedstrijden gevonden voor deze filters.")).toBeInTheDocument();
  });
});

function rows(container: HTMLElement): Element[] {
  return Array.from(container.querySelectorAll(".fixture-row"));
}
