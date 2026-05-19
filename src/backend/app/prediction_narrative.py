"""Research-context → leesbare AI-voorspelling (geen runtime-LLM)."""

from __future__ import annotations

import re
from typing import Any

from app.display_text import humanize_factor_reason, normalize_display_text
from app.teams import display_team_name

MATCH_SCOPED_IDS = frozenset(
    {
        "style_matchup",
        "opponent_profile_weak",
        "opponent_profile_strong",
        "tactical_weakness",
        "tactical_strength",
        "matchup_risk",
        "matchup_edge",
        "fixture_story",
        "psychology",
        "home_fixture",
        "away_fixture",
        "opener_context",
        "fixture_narrative",
        "discipline",
    }
)

FACTOR_LABELS: dict[str, str] = {
    "squad_load": "selectie",
    "distinctive_spark": "context",
    "star_dependency": "sterren",
    "selection_drama": "selectie",
    "crowd_bias": "publiek",
    "cohost_crowd": "co-host",
    "host_region": "co-host",
    "style_matchup": "tactiek",
    "opponent_profile_weak": "zwakte tegenstander",
    "opponent_profile_strong": "sterkte tegenstander",
    "tactical_weakness": "zwakte",
    "tactical_strength": "sterkte",
    "matchup_risk": "risico",
    "matchup_edge": "voordeel",
    "fixture_story": "context",
    "psychology": "mentaliteit",
    "home_fixture": "thuis",
    "away_fixture": "uit",
    "opener_context": "opener",
    "fixture_narrative": "context",
    "discipline": "discipline",
}

_REASON_PREFIX_RE = re.compile(
    r"^(tegenstander (zwak|sterk|kwetsbaar)|eigen (zwak|sterk)( punt)?|tegenstander)\s*:\s*",
    re.IGNORECASE,
)


def _label(factor_id: str) -> str:
    return FACTOR_LABELS.get(factor_id, factor_id.replace("_", " "))


def _side_factors(side: dict[str, Any], *, opponent_name: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    team_name = str(side.get("team") or "")
    for raw in side.get("reasons") or []:
        if not isinstance(raw, dict):
            continue
        factor_id = str(raw.get("id", ""))
        delta = int(raw.get("delta", 0))
        reason = humanize_factor_reason(
            str(raw.get("reason", "")).strip(),
            factor_id=factor_id,
            subject_team=team_name,
            opponent_team=opponent_name,
        )
        if not reason:
            continue
        out.append(
            {
                "id": factor_id,
                "delta": delta,
                "label": _label(factor_id),
                "reason": reason,
                "scope": "match" if factor_id in MATCH_SCOPED_IDS else "team",
            }
        )
    return out


def _nonzero_factors(factors: list[dict[str, object]]) -> list[dict[str, object]]:
    return [f for f in factors if int(f["delta"]) != 0]


def _tags(factors: list[dict[str, object]], team: str, *, limit: int = 4) -> list[str]:
    ranked = sorted(_nonzero_factors(factors), key=lambda f: abs(int(f["delta"])), reverse=True)
    return [f"{team}: {_label(str(f['id']))} {int(f['delta']):+d}" for f in ranked[:limit]]


def build_prediction_insight(
    *,
    home_team: str,
    away_team: str,
    pick: str,
    breakdown: dict[str, object],
    diff: int,
    stage: str,
    round_name: str,
) -> dict[str, object]:
    home_side = breakdown["home"]
    away_side = breakdown["away"]
    assert isinstance(home_side, dict) and isinstance(away_side, dict)

    home_name = str(home_side.get("team") or display_team_name(home_team))
    away_name = str(away_side.get("team") or display_team_name(away_team))
    home_power = int(home_side["powerScore"])
    away_power = int(away_side["powerScore"])
    home_ctx = int(home_side["contextDelta"])
    away_ctx = int(away_side["contextDelta"])
    home_eff = int(home_side["effectiveScore"])
    away_eff = int(away_side["effectiveScore"])

    home_factors = _side_factors(home_side, opponent_name=away_name)
    away_factors = _side_factors(away_side, opponent_name=home_name)

    verdict = _build_headline(pick, home_name, away_name)
    intro = _build_model_intro(home_name, away_name, home_eff, away_eff)
    components = _build_why_summary(
        pick,
        home_name,
        away_name,
        home_factors,
        away_factors,
        diff=diff,
    )

    steps = [
        {"title": "Hoe dit werkt", "body": intro},
        {"title": "Belangrijk in dit duel", "body": components},
    ]
    narrative = f"{intro}\n\n{components}"
    score_summary = f"Dueltotalen: {home_name} {home_eff}, {away_name} {away_eff}."

    winner_side = "home" if pick == "1" else "away" if pick == "2" else None

    return _insight_payload(
        score_summary=score_summary,
        verdict=verdict,
        narrative=narrative,
        steps=steps,
        tags=_tags(home_factors, home_name, limit=2) + _tags(away_factors, away_name, limit=2),
        diff=diff,
        home_name=home_name,
        away_name=away_name,
        home_power=home_power,
        away_power=away_power,
        home_ctx=home_ctx,
        away_ctx=away_ctx,
        home_eff=home_eff,
        away_eff=away_eff,
        home_factors=home_factors,
        away_factors=away_factors,
        winner_side=winner_side,
    )


def _build_headline(pick: str, home_name: str, away_name: str) -> str:
    if pick == "1":
        return f"De AI voorspelt dat {home_name} wint."
    if pick == "2":
        return f"De AI voorspelt dat {away_name} wint."
    return "De AI voorspelt een gelijkspel."


def _build_model_intro(home_name: str, away_name: str, home_eff: int, away_eff: int) -> str:
    return (
        f"Dit is berekend met ons AI-model. "
        f"Dueltotalen voor dit duel: {home_name} {home_eff}, {away_name} {away_eff}. "
        f"Dat is basissterkte plus kleine onderdelen uit de analyse van dit duel en de groepsfase."
    )


def _clean_reason_text(reason: str) -> str:
    text = reason.strip().rstrip(".")
    text = _REASON_PREFIX_RE.sub("", text).strip()
    if text:
        text = text[0].upper() + text[1:]
    return text


def _insight_key(reason: str, *team_names: str) -> str:
    text = _clean_reason_text(reason).lower()
    if "giménez" in text or "jiménez" in text:
        return "central-defenders-gimenez-jimenez"
    if "omschakeling" in text and "compact" in text:
        return "transition-vs-compact-block"
    for name in team_names:
        lowered = name.lower()
        text = text.replace(lowered, "")
        for part in re.split(r"[\s\-]+", lowered):
            if len(part) > 3:
                text = text.replace(part, "")
    return re.sub(r"\s+", " ", text).strip()[:80]


def _winner_loser(
    pick: str, home_name: str, away_name: str
) -> tuple[str | None, str | None]:
    if pick == "1":
        return home_name, away_name
    if pick == "2":
        return away_name, home_name
    return None, None


def _beat_kind(factor: dict[str, object], *, for_winner: bool) -> str | None:
    factor_id = str(factor["id"])
    delta = int(factor["delta"])
    reason_low = str(factor.get("reason", "")).lower()

    if for_winner and delta <= 0:
        return None
    if not for_winner and delta >= 0:
        return None

    if factor_id in ("host_region", "cohost_crowd", "home_fixture") and delta > 0:
        return "host"
    if factor_id == "style_matchup" and delta > 0:
        if any(w in reason_low for w in ("omschakeling", "compact", "transit", "press")):
            return "style"
    if factor_id == "opponent_profile_weak" and delta > 0:
        if "giménez" in reason_low or "jiménez" in reason_low:
            return "attack"
        return "matchup"
    if factor_id == "tactical_weakness" and delta < 0:
        if "giménez" in reason_low or "jiménez" in reason_low:
            return "attack"
        return "matchup"
    if factor_id in {"matchup_edge", "opponent_profile_strong", "matchup_risk"}:
        return "matchup"
    if factor_id == "opener_context" and delta < 0:
        return "matchup"
    return None


def _collect_story_kinds(
    winner: str,
    loser: str,
    winner_factors: list[dict[str, object]],
    loser_factors: list[dict[str, object]],
) -> dict[str, int]:
    """Sterkste signaal per thema (host / stijl / aanval)."""
    kinds: dict[str, int] = {}

    def consider(factor: dict[str, object], *, for_winner: bool) -> None:
        kind = _beat_kind(factor, for_winner=for_winner)
        if not kind:
            return
        weight = abs(int(factor["delta"]))
        if kind == "host":
            weight += 10
        kinds[kind] = max(kinds.get(kind, 0), weight)

    for factor in winner_factors:
        consider(factor, for_winner=True)
    for factor in loser_factors:
        consider(factor, for_winner=False)

    return kinds


def _compose_why_paragraph(winner: str, loser: str, kinds: dict[str, int]) -> str:
    has_host = "host" in kinds
    has_style = "style" in kinds
    has_attack = "attack" in kinds

    if has_host and has_style and has_attack:
        return (
            f"{winner} speelt thuis als co-host. "
            f"Hun spel past bij de compacte verdediging van {loser}, "
            f"terwijl {loser} weinig doelpuntenkansen haalt tegen Giménez en Jiménez achterin."
        )

    if has_host and has_style:
        return (
            f"{winner} speelt thuis als co-host. "
            f"Daarnaast past hun speelstijl, vooral snelle omschakeling, "
            f"bij hoe {loser} laag en compact verdedigt."
        )

    if has_host and has_attack:
        return (
            f"{winner} speelt thuis als co-host. "
            f"{loser} komt daarbij weinig door achterin bij Giménez en Jiménez."
        )

    if has_style and has_attack:
        return (
            f"Tactisch heeft {winner} het voordeel: hun omschakeling past bij de lage verdediging van {loser}, "
            f"en {loser} vindt weinig ruimte tegen Giménez en Jiménez achterin."
        )

    if has_host:
        return (
            f"{winner} heeft in dit duel een duidelijk thuisvoordeel als co-host; "
            f"dat weegt zwaarder dan de kleine tactische verschillen op het veld."
        )

    if has_style:
        return (
            f"{winner} heeft tactisch een match: hun spel met snelle omschakeling "
            f"past bij hoe {loser} laag en compact verdedigt."
        )

    if has_attack:
        return (
            f"{loser} creëert in de aanval weinig gevaar tegen het centrale duo "
            f"Giménez en Jiménez van {winner}."
        )

    if "matchup" in kinds:
        return (
            f"In de duelanalyse scoren een paar kleine tactische punten voor {winner}, "
            f"naast het grotere verschil in basissterkte."
        )

    return (
        f"De voorspelling steunt vooral op het verschil in basissterkte; "
        f"in dit duel vallen weinig extra signalen op."
    )


def _build_why_summary(
    pick: str,
    home_name: str,
    away_name: str,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
    *,
    diff: int,
) -> str:
    winner, loser = _winner_loser(pick, home_name, away_name)
    if not winner or not loser:
        if diff == 0:
            return (
                f"Het dueltotaal van {home_name} en {away_name} is gelijk; "
                f"het model ziet geen duidelijke winnaar. Een gelijkspel past daar het best bij."
            )
        return (
            f"Het verschil in dueltotaal is klein ({abs(diff)} punt{'en' if abs(diff) != 1 else ''}); "
            f"daarom is een gelijkspel de meest voorzichtige voorspelling."
        )

    winner_factors = home_factors if winner == home_name else away_factors
    loser_factors = away_factors if loser == away_name else home_factors

    kinds = _collect_story_kinds(winner, loser, winner_factors, loser_factors)
    if not kinds and abs(diff) >= 12:
        return (
            f"Het grote verschil tussen {winner} en {loser} zit vooral in de basissterkte; "
            f"de duelanalyse voegt daar weinig aan toe."
        )

    return _compose_why_paragraph(winner, loser, kinds)


def _insight_payload(
    *,
    score_summary: str,
    verdict: str,
    narrative: str,
    steps: list[dict[str, str]],
    tags: list[str],
    diff: int,
    home_name: str,
    away_name: str,
    home_power: int,
    away_power: int,
    home_ctx: int,
    away_ctx: int,
    home_eff: int,
    away_eff: int,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
    winner_side: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "scoreSummary": score_summary,
        "verdict": verdict,
        "narrative": narrative,
        "steps": steps,
        "tags": tags,
        "diff": diff,
        "home": {
            "team": home_name,
            "powerScore": home_power,
            "contextDelta": home_ctx,
            "effectiveScore": home_eff,
            "factors": home_factors,
        },
        "away": {
            "team": away_name,
            "powerScore": away_power,
            "contextDelta": away_ctx,
            "effectiveScore": away_eff,
            "factors": away_factors,
        },
    }
    if winner_side:
        payload["winnerSide"] = winner_side
    return payload
