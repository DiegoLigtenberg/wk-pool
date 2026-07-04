"""R32 90-min score distribution from synced results."""
from collections import Counter

from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.match_results_store import load_results, result_for_match
from app.tournament import load_fixtures

fixtures = load_fixtures()
store = load_results()
bracket = build_knockout_bracket_state(fixtures, store)

scores: list[str] = []
totals: list[int] = []
margins: list[int] = []
for fx in fixtures:
    if fx.round_number != "Round of 32":
        continue
    stored = result_for_match(store, fx.match_number)
    if not stored:
        continue
    h, a = int(stored["score"]["home"]), int(stored["score"]["away"])
    home, away = resolve_knockout_teams(fx, bracket)
    scores.append(f"{h}-{a}")
    totals.append(h + a)
    margins.append(abs(h - a))

print("R32 2026 (90 min) — 16 matches")
print("Scores:", Counter(scores))
print("Total goals:", Counter(totals))
print("Margin:", Counter(margins))
print("3+ for winner:", sum(1 for s in scores if max(int(s[0]), int(s[2])) >= 3))
print("4+ total:", sum(1 for t in totals if t >= 4))
