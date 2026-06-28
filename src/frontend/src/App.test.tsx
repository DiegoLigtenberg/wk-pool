import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { tournamentFixture } from "./test/tournamentFixture";

vi.mock("react-bracket-ui", () => ({
  Bracket: ({ matches }: { matches: unknown[] }) => <div data-testid="bracket">{matches.length} bracket matches</div>,
}));

describe("App", () => {
  it("loads the tournament and switches between the main views", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", fetchWith(tournamentFixture()));

    render(<App />);

    expect(screen.getByText("WK Pool laden...")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Volledig wedstrijdschema" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Poules" }));
    expect(screen.getByRole("heading", { name: "Live stand per poule" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Knock-out" }));
    expect(screen.getByRole("heading", { name: "Knock-outfase" })).toBeInTheDocument();
    expect(screen.getByTestId("bracket")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Crystal Ball" }));
    expect(screen.getByRole("heading", { name: "Toernooi-voorspellingen" })).toBeInTheDocument();
  });

  it("shows an error when the backend payload breaks the frontend contract", async () => {
    vi.stubGlobal("fetch", fetchWith({ summary: {} }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Backend-data komt niet overeen." })).toBeInTheDocument();
    expect(screen.getByText(/Ongeldige velden:/)).toBeInTheDocument();
  });
});

function fetchWith(payload: unknown): typeof fetch {
  return vi.fn(async () => ({
    ok: true,
    json: async () => payload,
  })) as unknown as typeof fetch;
}
