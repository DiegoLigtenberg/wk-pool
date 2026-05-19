import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { completedMatch } from "../../test/tournamentFixture";
import { PredictionPanel } from "./PredictionPanel";

describe("PredictionPanel", () => {
  it("keeps model intro inside details so the pick is not explained twice", () => {
    const match = {
      ...completedMatch,
      aiPrediction: {
        ...completedMatch.aiPrediction,
        pick: "2" as const,
        insight: {
          ...completedMatch.aiPrediction.insight!,
          verdict: "De AI voorspelt dat Schotland wint.",
          steps: [
            {
              title: "Hoe dit werkt",
              body: "Dit is berekend met ons AI-model. Dueltotalen voor dit duel: Haïti 59, Schotland 71.",
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
    expect(screen.getByText(/kleine tactische punten voor Schotland/)).toBeInTheDocument();

    const intros = container.querySelectorAll(".prediction-intro");
    expect(intros).toHaveLength(1);
    expect(intros[0]?.closest("details")).toBeTruthy();

    const lead = container.querySelector(".prediction-verdict--lead");
    const components = container.querySelector(".prediction-components");
    expect(lead?.compareDocumentPosition(components!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
