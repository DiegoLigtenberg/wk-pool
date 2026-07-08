from app.tournament import build_tournament_view

for m in build_tournament_view()["knockoutMatches"]:
    if m["round"] != "Quarter Finals":
        continue
    s = m["aiPrediction"].get("suggestedScore") or {}
    print(
        m["matchNumber"],
        m["homeTeam"],
        "vs",
        m["awayTeam"],
        "pick",
        m["aiPrediction"]["pick"],
        f"{s.get('home')}-{s.get('away')}",
        f"({m['aiPrediction']['homeWinProbability']}/{m['aiPrediction']['drawProbability']}/{m['aiPrediction']['awayWinProbability']}%)",
    )
