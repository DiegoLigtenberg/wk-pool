from app.tournament import build_tournament_view

t = build_tournament_view()
print("R16 suggested scores (90 min pool):\n")
high = []
for m in t["knockoutMatches"]:
    if m["round"] != "Round of 16":
        continue
    s = m["aiPrediction"].get("suggestedScore") or {}
    h, a = s.get("home", "?"), s.get("away", "?")
    total = h + a if isinstance(h, int) and isinstance(a, int) else None
    line = f"{m['matchNumber']:3} {m['homeTeam']:14} vs {m['awayTeam']:14} pick={m['aiPrediction']['pick']}  {h}-{a}"
    print(line)
    if isinstance(total, int) and (total >= 4 or h >= 3 or a >= 3):
        high.append(line)

print("\n--- High scores (3+ goals for one side, or 4+ total) ---")
for line in high:
    print(line)
