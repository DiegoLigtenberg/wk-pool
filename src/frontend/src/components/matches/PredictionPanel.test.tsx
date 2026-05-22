import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { completedMatch } from "../../test/tournamentFixture";
import { PredictionPanel } from "./PredictionPanel";

describe("PredictionPanel", () => {
  it("houdt model-uitleg en score-toelichting in research-details (geen dubbele pick-regel boven)", () => {
    const match = {
      ...completedMatch,
      aiPrediction: {
        ...completedMatch.aiPrediction,
        pick: "2" as const,
        insight: {
          ...completedMatch.aiPrediction.insight!,
          verdict: "De AI voorspelt dat Schotland wint.",
          pickLogicNote: "",
          steps: [
            {
              title: "Hoe dit werkt",
              body: "Dit rekent ons AI-model uit in één getal per team: basissterkte plus aanpassingen uit Haïti–Schotland en uit de hele groepsfase. In de kaarten hieronder zie je het totaal (wedstrijdscore) en welke onderdelen meetellen (+ en −).",
            },
            {
              title: "Belangrijk in dit duel",
              body: "In de duelanalyse scoren een paar kleine tactische punten voor Schotland.",
            },
          ],
        },
      },
    };

    const { container } = render(
      <PredictionPanel
        id="prediction-test"
        match={match}
        onClose={() => undefined}
        closeButtonRef={{ current: null }}
      />,
    );

    expect(screen.getByText("De AI voorspelt dat Schotland wint.")).toBeInTheDocument();
    expect(screen.getByText(/Mexico speelt thuis als co-host/)).toBeInTheDocument();

    const intros = container.querySelectorAll(".prediction-intro");
    expect(intros).toHaveLength(1);
    expect(intros[0]?.closest("details")).toBeTruthy();

    const lead = container.querySelector(".prediction-verdict--lead");
    const summary = container.querySelector(".prediction-lead-summary");
    expect(lead?.compareDocumentPosition(summary!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const leadSummary = container.querySelector(".prediction-lead-summary");
    expect(leadSummary?.textContent?.toLowerCase()).not.toContain("wedstrijdscore");

    expect(container.querySelector(".prediction-pick-reason")).toBeNull();

    expect(container.querySelector(".prediction-suggested-score")).toBeNull();
    expect(container.querySelector(".prediction-match-stats")).toBeNull();
    expect(container.querySelector(".prediction-pick-steps")).toBeNull();
    expect(screen.getByText("Scores en research-details")).toBeInTheDocument();
  });
});
