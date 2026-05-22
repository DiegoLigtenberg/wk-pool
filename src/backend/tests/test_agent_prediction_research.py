"""Agent checks: prediction/narrative + research/context pipeline (CI)."""

from __future__ import annotations

import re

from app.data.teams.context_scoring_builder import _mentions_opponent, build_context_scoring
from app.display_text import humanize_matchup_shorthand, is_cryptic_reason
from app.teams import display_team_name
from app.data.teams.context_score import match_context_breakdown
from app.data.teams.team_loader import load_all_bundles
from app.predictions import predict_match
from app.teams import fifa_team_key

SCORE_TERMS_IN_LEAD = (
    "wedstrijdscore",
    "verschil in wedstrijdscore",
    " punten verschil",
)

BROKEN_NARRATIVE_MARKERS = (
    "speelt thuis in mexico opent",
    "zuid-afrika opent als co-host",
)

VAGUE_NARRATIVE_MARKERS = (
    "thuisvoordeel als co-host",
    "weegt zwaarder",
    "kleine tactische verschillen",
    "kleine tactische punten",
    "in dit duel speelt mee",
    "vallen weinig extra signalen",
    "ondersteunt de voorspelling",
    "het model ziet geen duidelijke",
)

GOLDEN_DUELS = (
    ("Canada", "Bosnia and Herzegovina", "I"),
    ("Haiti", "Scotland", "L"),
    ("Germany", "Curaçao", "E"),
    ("Netherlands", "Japan", "E"),
)

def _all_group_duels() -> list[tuple[str, str]]:
    bundles = load_all_bundles()
    pairs: list[tuple[str, str]] = []
    for fifa, bundle in bundles.items():
        for opp in bundle.group_stage.opponents_fifa:
            opp_key = fifa_team_key(opp)
            if opp_key in bundles:
                pairs.append((fifa, opp_key))
    return pairs


def test_lead_summary_never_mentions_score_points() -> None:
    """Zichtbare tekst vóór uitklap: geen wedstrijdscore-cijfers."""
    failures: list[str] = []
    for home, away in _all_group_duels():
        pred = predict_match(home, away, "group", "1", None)
        ins = pred["insight"]
        lead = str(ins.get("leadSummary") or ins["steps"][1]["body"])
        verdict = str(ins["verdict"])
        visible = f"{verdict} {lead}".lower()
        for term in SCORE_TERMS_IN_LEAD:
            if term in visible:
                failures.append(f"{home}–{away}: lead contains {term!r}")
        if re.search(r"\d+\s+punten", visible):
            failures.append(f"{home}–{away}: lead contains N punten")
    assert not failures, "\n".join(failures[:15])


def test_all_group_narratives_avoid_vague_templates() -> None:
    failures: list[str] = []
    for home, away in _all_group_duels():
        pred = predict_match(home, away, "group", "1", None)
        why = str(pred["insight"]["steps"][1]["body"]).lower()
        if len(why.strip()) < 28:
            failures.append(f"{home}–{away}: too short ({why!r})")
        for marker in BROKEN_NARRATIVE_MARKERS:
            if marker in why:
                failures.append(f"{home}–{away}: broken phrasing {marker!r}")
        for marker in VAGUE_NARRATIVE_MARKERS:
            if marker in why:
                failures.append(f"{home}–{away}: contains {marker!r}")
    assert not failures, "\n".join(failures[:20])


def test_pick_aligns_with_probabilities() -> None:
    """Pick = hoogste kans (1 thuis, 2 uit, 3 gelijk in groep)."""
    failures: list[str] = []
    for home, away in _all_group_duels():
        pred = predict_match(home, away, "group", "1", None)
        pick = str(pred["pick"])
        h = int(pred["homeWinProbability"] or 0)
        d = int(pred["drawProbability"] or 0)
        a = int(pred["awayWinProbability"] or 0)
        if pick == "1" and not (h >= d and h >= a):
            failures.append(f"{home}–{away}: pick 1 but % {h}/{d}/{a}")
        if pick == "2" and not (a >= d and a >= h):
            failures.append(f"{home}–{away}: pick 2 but % {h}/{d}/{a}")
        if pick == "3" and not (d >= h and d >= a):
            failures.append(f"{home}–{away}: pick 3 but % {h}/{d}/{a}")
    assert not failures, "\n".join(failures[:15])


def test_pick_direction_matches_dueltotaal() -> None:
    from app.pool_edge import apply_adjustments, collect_pick_adjustments
    from app.predictions import _pick_from_diff

    failures: list[str] = []
    for home, away in _all_group_duels():
        pred = predict_match(home, away, "group", "1", None)
        ins = pred["insight"]
        pick = str(pred["pick"])
        br_diff = int(ins["baseDiff"])
        hp, ap = int(ins["home"]["powerScore"]), int(ins["away"]["powerScore"])
        adj = collect_pick_adjustments(
            home_key=home,
            away_key=away,
            home_power=hp,
            away_power=ap,
            home_factors=ins["home"]["factors"],
            away_factors=ins["away"]["factors"],
        )
        adjusted = apply_adjustments(br_diff, adj)
        expected = _pick_from_diff(
            adjusted, can_draw=True, home_power=hp, away_power=ap
        )
        if pick != expected:
            failures.append(
                f"{home}–{away}: pick {pick} expected {expected} (adj diff {adjusted})"
            )
    assert not failures, "\n".join(failures[:15])


def test_stored_context_scoring_matches_fresh_build() -> None:
    """Research-YAML context_scoring mag niet achterlopen op builder-logica."""
    bundles = load_all_bundles()
    stale: list[str] = []
    for fifa, bundle in bundles.items():
        if bundle.context_scoring is None:
            stale.append(f"{bundle.team_name_nl}: missing context_scoring block")
            continue
        fresh = build_context_scoring(bundle, bundles)
        stored = bundle.context_scoring
        sp = {(f.id, f.delta, f.reason) for f in stored.persistent}
        fp = {(f.id, f.delta, f.reason) for f in fresh.persistent}
        if sp != fp:
            stale.append(f"{bundle.team_name_nl}: stale persistent")
        for opp in bundle.group_stage.opponents_fifa:
            ok = fifa_team_key(opp)
            sv = {(f.id, f.delta, f.reason) for f in stored.versus.get(ok, ())}
            fv = {(f.id, f.delta, f.reason) for f in fresh.versus.get(ok, ())}
            if sv != fv:
                stale.append(f"{bundle.team_name_nl} vs {ok}: stale versus")
    assert not stale, "\n".join(stale[:25])


def _is_stub_matchup_line(text: str) -> bool:
    """Alleen landnaam of label zonder context (geen spaties/slash)."""
    t = text.strip().rstrip(".")
    if " " in t or "/" in t or "-" in t:
        return False
    return len(t) < 22


def test_research_matchup_bullets_not_cryptic_stubs() -> None:
    bundles = load_all_bundles()
    bad: list[str] = []
    for fifa, bundle in bundles.items():
        for opp_fifa in bundle.group_stage.opponents_fifa:
            opp_nl = display_team_name(opp_fifa)
            for field, lines in (
                ("matchup_counters_us", bundle.matchup_counters_us),
                ("matchup_we_counter", bundle.matchup_we_counter),
            ):
                for line in lines:
                    if not _is_stub_matchup_line(line):
                        continue
                    if not _mentions_opponent(line, opp_nl, opp_fifa):
                        continue
                    humanized = humanize_matchup_shorthand(
                        line,
                        opp_nl,
                        team_nl=bundle.team_name_nl,
                        kind="risk" if field == "matchup_counters_us" else "edge",
                    )
                    if is_cryptic_reason(humanized):
                        bad.append(
                            f"{bundle.team_name_nl} {field} vs {opp_nl}: "
                            f"{line.strip()!r} -> {humanized!r}"
                        )
    assert not bad, "\n".join(bad[:25])


def test_golden_duels_regression() -> None:
    canada = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    why_ca = canada["insight"]["steps"][1]["body"].lower()
    assert canada["pick"] in ("1", "3")
    assert "thuisvoordeel als co-host" not in why_ca
    assert any(w in why_ca for w in ("toronto", "co-host", "keeper", "st. clair"))

    haiti_br = match_context_breakdown(fifa_team_key("Haiti"), fifa_team_key("Scotland"))
    away_ids = {r["id"] for r in haiti_br["away"]["reasons"]}
    assert "style_matchup" not in away_ids or not any(
        r["id"] == "style_matchup" and r["delta"] < 0 for r in haiti_br["away"]["reasons"]
    )

    ger = predict_match("Germany", "Curaçao", "group", "1", "E")
    home_ids = {r["id"] for r in ger["insight"]["home"]["factors"] if r["delta"]}
    assert "opponent_profile_strong" not in home_ids

    nl = predict_match("Netherlands", "Japan", "group", "1", "E")
    why_nl = nl["insight"]["steps"][1]["body"].lower()
    assert " lean " not in f" {why_nl} "
    assert any(w in why_nl for w in ("simons", "japan", "moriyasu", "omschakeling", "compact"))


def test_cohost_host_region_not_double_counted_in_narrative_only() -> None:
    """Co-host +3 host_region is bewust; narrative mag niet generiek dubbel klinken."""
    pred = predict_match("Canada", "Bosnia and Herzegovina", "group", "1", "I")
    why = pred["insight"]["steps"][1]["body"].lower()
    assert why.count("co-host") <= 3
    assert "weegt zwaarder" not in why
