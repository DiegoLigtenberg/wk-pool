import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { TeamInsightProvider } from "../cards/TeamInsightContext";
import { tournamentFixture } from "../../test/tournamentFixture";
import { allMatches } from "../../lib/tournament";
import { MatchesView } from "./MatchesView";

function renderMatchesView() {
  const tournament = tournamentFixture();
  const view = render(
    <TeamInsightProvider insights={tournament.teamInsights} openTeam={() => undefined}>
      <MatchesView matches={allMatches(tournament)} summary={tournament.summary} />
    </TeamInsightProvider>,
  );
  return { tournament, ...view };
}

describe("MatchesView", () => {
  it("filters matches and can reveal an AI explanation", async () => {
    const user = userEvent.setup();
    const { container } = renderMatchesView();

    expect(rows(container)).toHaveLength(2);

    await user.click(screen.getByRole("combobox", { name: "Toon Alle wedstrijden" }));
    await user.click(screen.getByRole("option", { name: "Gespeeld" }));
    expect(rows(container)).toHaveLength(1);
    expect(screen.getByText("2 - 0")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Toon AI-uitleg voor Mexico tegen Zuid-Afrika" }));
    expect(screen.getByText("De AI voorspelt dat Mexico wint.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sluiten" }));
    expect(screen.queryByText("De AI voorspelt dat Mexico wint.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("combobox", { name: "Fase Alle fases" }));
    await user.click(screen.getByRole("option", { name: "Knock-out" }));

    expect(rows(container)).toHaveLength(1);
    expect(screen.getByRole("combobox", { name: "Toon Alle wedstrijden" })).toBeInTheDocument();

    await user.click(screen.getByRole("combobox", { name: "Land Alle landen" }));
    await user.click(screen.getByRole("option", { name: "Mexico" }));

    expect(rows(container)).toHaveLength(1);
    expect(screen.getByRole("combobox", { name: "Fase Alle fases" })).toBeInTheDocument();
    expect(screen.getByText("2 - 0")).toBeInTheDocument();
  });

  it("opens the AI panel when clicking the score, not the team name", async () => {
    const user = userEvent.setup();
    renderMatchesView();

    await user.click(screen.getByText("2 - 0"));
    expect(screen.getByText("De AI voorspelt dat Mexico wint.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sluiten" }));
    expect(screen.queryByText("De AI voorspelt dat Mexico wint.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Open teamvisie voor Mexico" }));
    expect(screen.queryByText("De AI voorspelt dat Mexico wint.")).not.toBeInTheDocument();
  });

  it("keeps only one AI panel open and closes when clicking outside", async () => {
    const user = userEvent.setup();
    const { container } = renderMatchesView();
    const fixtureRows = rows(container);

    await user.click(within(fixtureRows[0] as HTMLElement).getByText("2 - 0"));
    expect(screen.getByText("De AI voorspelt dat Mexico wint.")).toBeInTheDocument();

    await user.click(within(fixtureRows[1] as HTMLElement).getByText("-"));
    expect(screen.queryByText("De AI voorspelt dat Mexico wint.")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".prediction-panel")).toHaveLength(1);

    await user.click(screen.getByRole("heading", { name: "Volledig wedstrijdschema" }));
    expect(container.querySelectorAll(".prediction-panel")).toHaveLength(0);
  });
});

function rows(container: HTMLElement): Element[] {
  return Array.from(container.querySelectorAll(".fixture-row"));
}
