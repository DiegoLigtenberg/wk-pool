"""Quick audit: R32 picks/scores vs actual; R16 bracket resolution."""
from __future__ import annotations

from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.group_form import build_group_form_index
from app.knockout_form import build_knockout_round_form_index
from app.match_results_store import load_results, result_for_match
from app.predictions import is_known_team, predict_match
from app.tournament import load_fixtures


def main() -> None:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form_index = build_group_form_index(fixtures, store) if bracket else {}
    ko_form = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round="Round of 16"
        )
        if bracket
        else {}
    )

    r32 = [fx for fx in fixtures if fx.round_number == "Round of 32"]
    print("=== R32 audit ===")
    pick_ok = 0
    for fx in sorted(r32, key=lambda f: f.match_number):
        home, away = resolve_knockout_teams(fx, bracket)
        gf = (form_index.get(home), form_index.get(away))
        pred = predict_match(
            home,
            away,
            "knockout",
            fx.round_number,
            None,
            match_number=fx.match_number,
            group_forms=gf,
        )
        stored = result_for_match(store, fx.match_number)
        if not stored:
            print(f"{fx.match_number}: {home} vs {away} — no result")
            continue
        score = stored["score"]
        hg, ag = int(score["home"]), int(score["away"])
        adv = stored.get("advancingTeam")
        if hg > ag:
            actual = "1"
        elif ag > hg:
            actual = "2"
        else:
            actual = "3"
        pick = str(pred["pick"])
        ok = pick == actual
        if ok:
            pick_ok += 1
        sug = pred.get("suggestedScore") or {}
        sh, sa = sug.get("home", "?"), sug.get("away", "?")
        flag = "OK" if ok else "MISS"
        print(
            f"{fx.match_number} {home} vs {away}: pred {pick} ({sh}-{sa}) "
            f"actual {actual} ({hg}-{ag}) adv={adv} [{flag}]"
        )
    print(f"Pick accuracy: {pick_ok}/{len(r32)}")

    print("\n=== R16 bracket ===")
    r16 = [fx for fx in fixtures if fx.round_number == "Round of 16"]
    for fx in sorted(r16, key=lambda f: f.match_number):
        home, away = resolve_knockout_teams(fx, bracket)
        known = is_known_team(home) and is_known_team(away)
        gf = (form_index.get(home), form_index.get(away))
        kf = (ko_form.get(home), ko_form.get(away))
        pred = (
            predict_match(
                home,
                away,
                "knockout",
                fx.round_number,
                None,
                match_number=fx.match_number,
                group_forms=gf,
                knockout_forms=kf,
            )
            if known
            else None
        )
        pick = pred["pick"] if pred else "?"
        sug = (pred or {}).get("suggestedScore") or {}
        score_txt = f"{sug.get('home','?')}-{sug.get('away','?')}" if pred else "-"
        print(f"{fx.match_number}: {home} vs {away} | pick={pick} score={score_txt}")


if __name__ == "__main__":
    main()
