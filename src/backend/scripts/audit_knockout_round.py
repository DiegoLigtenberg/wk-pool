"""Audit QF results vs predictions; show SF bracket + predictions."""
from __future__ import annotations

from app.group_form import build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.knockout_form import build_knockout_round_form_index
from app.match_results_store import load_results, result_for_match
from app.predictions import is_known_team, predict_match
from app.tournament import load_fixtures


def actual_pick(score: dict) -> str:
    h, a = int(score["home"]), int(score["away"])
    if h > a:
        return "1"
    if a > h:
        return "2"
    return "3"


def audit_round(round_name: str, ko_before: str) -> tuple[int, int]:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form = build_group_form_index(fixtures, store) if bracket else {}
    ko_prior = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round=ko_before
        )
        if bracket
        else {}
    )

    print(f"\n{'='*60}\n{round_name} — results vs predictions\n{'='*60}")
    ok = total = 0
    for fx in sorted(fixtures, key=lambda f: f.match_number):
        if fx.round_number != round_name:
            continue
        home, away = resolve_knockout_teams(fx, bracket)
        stored = result_for_match(store, fx.match_number)
        gf = (form.get(home), form.get(away))
        kf = (ko_prior.get(home), ko_prior.get(away))
        pred = predict_match(
            home,
            away,
            "knockout",
            fx.round_number,
            None,
            match_number=fx.match_number,
            group_forms=gf,
            knockout_forms=kf,
        )
        pick = str(pred["pick"])
        sug = pred.get("suggestedScore") or {}
        sh, sa = sug.get("home", "?"), sug.get("away", "?")

        if not stored:
            print(f"{fx.match_number:3} {home:16} vs {away:16}  — upcoming  pred {pick} ({sh}-{sa})")
            continue

        total += 1
        act = actual_pick(stored["score"])
        hg, ag = int(stored["score"]["home"]), int(stored["score"]["away"])
        hit = pick == act
        if hit:
            ok += 1
        flag = "OK" if hit else "MISS"
        print(
            f"{fx.match_number:3} {home:16} vs {away:16}  "
            f"pred {pick} ({sh}-{sa})  actual {act} ({hg}-{ag})  [{flag}]"
        )

    if total:
        print(f"\nPick: {ok}/{total}")
    return ok, total


def show_predictions(round_name: str, ko_before: str) -> None:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form = build_group_form_index(fixtures, store) if bracket else {}
    ko_prior = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round=ko_before
        )
        if bracket
        else {}
    )

    print(f"\n{'='*60}\n{round_name} — predictions\n{'='*60}")
    for fx in sorted(fixtures, key=lambda f: f.match_number):
        if fx.round_number != round_name:
            continue
        home, away = resolve_knockout_teams(fx, bracket)
        if not (is_known_team(home) and is_known_team(away)):
            print(f"{fx.match_number:3} TBA vs TBA")
            continue
        gf = (form.get(home), form.get(away))
        kf = (ko_prior.get(home), ko_prior.get(away))
        pred = predict_match(
            home,
            away,
            "knockout",
            fx.round_number,
            None,
            match_number=fx.match_number,
            group_forms=gf,
            knockout_forms=kf,
        )
        sug = pred.get("suggestedScore") or {}
        print(
            f"{fx.match_number:3} {home:16} vs {away:16}  "
            f"pick={pred['pick']}  score={sug.get('home')}-{sug.get('away')}  "
            f"({pred['homeWinProbability']}/{pred['drawProbability']}/{pred['awayWinProbability']}%)"
        )


if __name__ == "__main__":
    audit_round("Quarter Finals", "Quarter Finals")
    show_predictions("Semi Finals", "Semi Finals")
