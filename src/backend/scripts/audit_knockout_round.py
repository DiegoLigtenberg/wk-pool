"""Audit R16 results vs predictions; show QF bracket + predictions."""
from __future__ import annotations

from app.group_form import build_group_form_index
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.knockout_form import build_knockout_round_form_index
from app.match_results_store import load_results, result_for_match
from app.predictions import is_known_team, predict_match
from app.tournament import load_fixtures, build_tournament_view


def actual_pick(score: dict) -> str:
    h, a = int(score["home"]), int(score["away"])
    if h > a:
        return "1"
    if a > h:
        return "2"
    return "3"


def audit_round(round_name: str) -> tuple[int, int]:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form = build_group_form_index(fixtures, store) if bracket else {}
    ko_before_r16 = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round="Round of 16"
        )
        if bracket
        else {}
    )
    ko_before_qf = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round="Quarter Finals"
        )
        if bracket
        else {}
    )

    print(f"\n{'='*60}\n{round_name} — results vs predictions\n{'='*60}")
    ok = total = 0
    exact = 0
    for fx in sorted(fixtures, key=lambda f: f.match_number):
        if fx.round_number != round_name:
            continue
        home, away = resolve_knockout_teams(fx, bracket)
        stored = result_for_match(store, fx.match_number)
        gf = (form.get(home), form.get(away))
        kf = (ko_before_r16.get(home), ko_before_r16.get(away))
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
            print(f"{fx.match_number:3} {home:16} vs {away:16}  — nog niet gespeeld  pred {pick} ({sh}-{sa})")
            continue

        total += 1
        act = actual_pick(stored["score"])
        hg, ag = int(stored["score"]["home"]), int(stored["score"]["away"])
        hit = pick == act
        if hit:
            ok += 1
        if isinstance(sh, int) and isinstance(sa, int) and sh == hg and sa == ag:
            exact += 1
        flag = "OK" if hit else "MISS"
        score_hit = "exact!" if isinstance(sh, int) and sh == hg and sa == ag else ""
        print(
            f"{fx.match_number:3} {home:16} vs {away:16}  "
            f"pred {pick} ({sh}-{sa})  actual {act} ({hg}-{ag})  [{flag}] {score_hit}"
        )

    if total:
        print(f"\nPick: {ok}/{total}  |  Exact score: {exact}/{total}")
    return ok, total


def show_qf_predictions() -> None:
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    form = build_group_form_index(fixtures, store) if bracket else {}
    ko_form = (
        build_knockout_round_form_index(
            fixtures, store, bracket.resolved_teams, before_round="Quarter Finals"
        )
        if bracket
        else {}
    )

    print(f"\n{'='*60}\nQuarter-finals — bracket + predictions\n{'='*60}")
    for fx in sorted(fixtures, key=lambda f: f.match_number):
        if fx.round_number != "Quarter Finals":
            continue
        home, away = resolve_knockout_teams(fx, bracket)
        known = is_known_team(home) and is_known_team(away)
        if not known:
            print(f"{fx.match_number:3} TBA vs TBA  (wacht op R16-winnaars)")
            continue
        gf = (form.get(home), form.get(away))
        kf = (ko_form.get(home), ko_form.get(away))
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
            f"conf={pred['confidence']}%"
        )


if __name__ == "__main__":
    audit_round("Round of 16")
    show_qf_predictions()
