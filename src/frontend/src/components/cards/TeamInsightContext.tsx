import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { TeamInsight } from "../../types";

type TeamInsightContextValue = {
  insights: Record<string, TeamInsight>;
  openTeam: (team: string) => void;
};

const TeamInsightContext = createContext<TeamInsightContextValue | null>(null);

export function TeamInsightProvider({
  insights,
  openTeam,
  children,
}: TeamInsightContextValue & { children: ReactNode }) {
  return <TeamInsightContext.Provider value={{ insights, openTeam }}>{children}</TeamInsightContext.Provider>;
}

export function useTeamInsight(team: string) {
  const context = useContext(TeamInsightContext);
  if (!context) {
    return { insight: null, open: null };
  }

  return {
    insight: context.insights[team] ?? null,
    open: () => context.openTeam(team),
  };
}
