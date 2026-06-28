"""Research-context → leesbare AI-voorspelling (geen runtime-LLM)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.data.teams.factor_dedupe import MATCH_SCOPED_IDS
from app.data.teams.team_loader import get_team_bundle
from app.display_text import (
    humanize_factor_reason,
    looks_truncated_reason,
    normalize_display_text,
)
from app.teams import display_team_name

_MATCH_NEGATIVE_IDS = frozenset(
    {
        "fixture_story",
        "matchup_risk",
        "opener_context",
        "psychology",
        "discipline",
        "choke_risk",
    }
)

FACTOR_LABELS: dict[str, str] = {
    "squad_load": "blessures",
    "distinctive_spark": "context",
    "star_dependency": "sterren",
    "selection_drama": "selectiedruk",
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
    "upset_path": "upset-kans",
    "choke_risk": "choke-risico",
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
_GENERIC_PROFITEERT_RE = re.compile(
    r"profiteert van de speelstijl van .+ in dit duel\.?$", re.I
)
_VENUE_ONLY_RE = re.compile(
    r"^.+\s+stadium.*\(co-host\)\.?$", re.I
)
_STYLE_MATCHUP_RE = re.compile(
    r"omschakeling past bij het (lage, )?compacte blok|compacte blok van|snel om te schakelen",
    re.I,
)
_TEAM_BACKGROUND_IDS = frozenset(
    {"distinctive_spark", "selection_drama", "squad_load"}
)
_DEPRIORITIZED_LEAD_IDS = frozenset({"style_matchup", "matchup_edge"})


def _label(factor_id: str) -> str:
    return FACTOR_LABELS.get(factor_id, factor_id.replace("_", " "))


_COHOST_TEAM_LAYER_IDS = frozenset({"cohost_crowd", "host_region"})


def _drop_duplicate_cohost_home_fixture(
    factors: list[dict[str, object]],
) -> list[dict[str, object]]:
    """UI: geen tweede regel met dezelfde co-host-tekst als thuis + co-host."""
    primary = next(
        (
            f
            for f in factors
            if str(f.get("id")) == "cohost_crowd" and int(f.get("delta", 0)) > 0
        ),
        None,
    )
    if primary is None:
        return factors
    primary_reason = str(primary.get("reason", "")).strip().lower()
    if not primary_reason:
        return factors
    return [
        f
        for f in factors
        if not (
            str(f.get("id")) == "home_fixture"
            and str(f.get("reason", "")).strip().lower() == primary_reason
        )
    ]


def _collapse_cohost_factors_for_display(
    factors: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Samenvoegen dubbele co-host op groepsniveau (cohost_crowd + host_region)."""
    factors = _drop_duplicate_cohost_home_fixture(factors)
    team_cohost = [
        f
        for f in factors
        if str(f.get("id")) in _COHOST_TEAM_LAYER_IDS and int(f.get("delta", 0)) > 0
    ]
    if len(team_cohost) <= 1:
        return factors

    primary = next(
        (f for f in team_cohost if str(f.get("id")) == "cohost_crowd"),
        team_cohost[0],
    )
    drop_ids = {str(f["id"]) for f in team_cohost if f is not primary}
    merged_delta = sum(int(f.get("delta", 0)) for f in team_cohost)
    merged = {**primary, "delta": merged_delta, "label": "co-host", "scope": "team"}

    out: list[dict[str, object]] = []
    inserted = False
    for factor in factors:
        fid = str(factor.get("id"))
        if fid in drop_ids:
            continue
        if fid == str(primary.get("id")) and not inserted:
            out.append(merged)
            inserted = True
            continue
        if fid in _COHOST_TEAM_LAYER_IDS and int(factor.get("delta", 0)) > 0:
            continue
        out.append(factor)
    if not inserted:
        out.append(merged)
    return out


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
    return _collapse_cohost_factors_for_display(out)


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
    base_diff: int | None = None,
    pool_adjustments: list[dict[str, object]] | None = None,
    pick_logic_note: str = "",
    pick_score_note: str = "",
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
    intro = _build_model_intro(home_name, away_name, stage=stage)
    research_diff = base_diff if base_diff is not None else diff
    lead_summary = _build_lead_summary(
        pick,
        home_name,
        away_name,
        home_factors,
        away_factors,
        diff=research_diff,
        home_group_opponents=_group_opponent_names_nl(home_team),
        away_group_opponents=_group_opponent_names_nl(away_team),
    )
    if not lead_summary.strip() and pool_adjustments:
        lead_summary = _lead_from_pool_adjustments(pool_adjustments)

    score_summary = _build_score_summary(
        home_name, away_name, home_eff, away_eff, diff=research_diff
    )
    if pick_score_note.strip():
        score_summary = f"{score_summary} {pick_score_note}"
    steps = [
        {"title": "Hoe dit werkt", "body": intro},
        {"title": "Belangrijk in dit duel", "body": lead_summary},
    ]
    narrative = f"{verdict}\n\n{lead_summary}\n\n{intro}\n\n{score_summary}"

    winner_side = "home" if pick == "1" else "away" if pick == "2" else None

    return _insight_payload(
        score_summary=score_summary,
        lead_summary=lead_summary,
        verdict=verdict,
        narrative=narrative,
        steps=steps,
        tags=_tags(home_factors, home_name, limit=2) + _tags(away_factors, away_name, limit=2),
        diff=diff,
        base_diff=research_diff,
        pick_logic_note=pick_logic_note,
        pool_adjustments=pool_adjustments or [],
        home_name=home_name,
        away_name=away_name,
        home_power=home_power,
        away_power=away_power,
        home_ctx=home_ctx,
        away_ctx=away_ctx,
        home_research=int(home_side.get("researchDelta", 0)),
        home_host=int(home_side.get("hostDelta", 0)),
        home_travel=int(home_side.get("travelDelta", 0)),
        home_eff=home_eff,
        away_research=int(away_side.get("researchDelta", 0)),
        away_host=int(away_side.get("hostDelta", 0)),
        away_travel=int(away_side.get("travelDelta", 0)),
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


def _build_model_intro(home_name: str, away_name: str, *, stage: str) -> str:
    """Korte uitleg onder 'Scores en research-details'; geen herhaling met score-regels."""
    phase = "de hele groepsfase" if stage == "group" else "eerdere knock-outrondes"
    return (
        f"Dit rekent ons AI-model uit in één getal per team: basissterkte plus aanpassingen uit "
        f"{home_name}–{away_name} en uit {phase}. "
        f"In de kaarten hieronder zie je het totaal (wedstrijdscore) en welke onderdelen meetellen "
        f"(+ en −)."
    )


def _build_score_summary(
    home_name: str,
    away_name: str,
    home_eff: int,
    away_eff: int,
    *,
    diff: int,
) -> str:
    """Compacte samenvatting voor API; scores staan in de UI-kaarten."""
    if diff == 0:
        return f"Wedstrijdscore gelijk: {home_name} {home_eff}, {away_name} {away_eff}."
    leader, trailer, lead_eff, trail_eff = (
        (home_name, away_name, home_eff, away_eff)
        if home_eff > away_eff
        else (away_name, home_name, away_eff, home_eff)
    )
    gap = abs(diff)
    punt = "punt" if gap == 1 else "punten"
    return (
        f"{leader} {lead_eff} – {trailer} {trail_eff} "
        f"({gap} {punt} verschil in wedstrijdscore)."
    )


def _after_colon_clause(text: str) -> str:
    """Tekst na dubbele punt; geen kapitalisatie van eigennamen verstoren."""
    return text.strip()


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


_HOST_FACTOR_IDS = frozenset({"host_region", "cohost_crowd", "home_fixture"})
_LOSER_CONTRAST_PLAIN_IDS = frozenset({"away_fixture", "home_fixture"})


def _narrate_host_bundle(
    winner: str,
    opponent: str,
    factors: list[dict[str, object]],
    *,
    group_opponents: list[str] | None = None,
) -> str:
    """Co-host in één zin met stad of publiek, geen vage 'thuisvoordeel'-tekst."""
    has_host = any(
        str(f["id"]) == "host_region" and int(f["delta"]) > 0 for f in factors
    )
    home_fx = next(
        (f for f in factors if str(f["id"]) == "home_fixture" and int(f["delta"]) > 0),
        None,
    )
    crowd = next(
        (
            f
            for f in factors
            if str(f["id"]) in ("cohost_crowd", "crowd_bias") and int(f["delta"]) > 0
        ),
        None,
    )
    # Co-host kan alleen als cohost_crowd binnenkomen (zonder host_region/home_fixture).
    if not has_host and not home_fx and not crowd:
        return ""

    if home_fx:
        venue = _clean_reason_text(str(home_fx["reason"]))
        low = venue.lower()
        if low.startswith("thuis in "):
            venue = venue[9:]
        if low.startswith(winner.lower()) or "opent" in low or "co-host" in low:
            return normalize_display_text(venue)
        return normalize_display_text(f"{winner} speelt thuis in {venue}")

    if crowd:
        detail = _clean_reason_text(str(crowd["reason"]))
        if str(crowd["id"]) == "crowd_bias":
            return normalize_display_text(detail)
        if not _include_persistent_cohost_story(winner, opponent, group_opponents):
            return ""
        if winner.lower() in detail.lower()[:20]:
            return normalize_display_text(detail)
        return normalize_display_text(
            f"{winner} speelt als co-host met thuispubliek: {detail[0].lower()}{detail[1:]}"
        )

    if not _include_persistent_cohost_story(winner, opponent, group_opponents):
        return ""
    return normalize_display_text(
        f"{winner} speelt in eigen regio als co-host, met thuispubliek en korte reizen"
    )


def _sentence_from_factor(
    factor: dict[str, object],
    *,
    winner: str,
    loser: str,
    for_team: str,
    contrast: bool = False,
) -> str:
    """Eén factor → leesbare zin uit de research-reden."""
    reason = _clean_reason_text(str(factor.get("reason", "")))
    if not reason or looks_truncated_reason(reason):
        return ""
    fid = str(factor["id"])
    delta = int(factor["delta"])

    if fid in _HOST_FACTOR_IDS and delta > 0:
        return ""

    scope = str(factor.get("scope", ""))
    if (
        fid in _MATCH_NEGATIVE_IDS
        and delta < 0
        and scope == "match"
    ):
        return normalize_display_text(_after_colon_clause(reason))

    if fid in ("selection_drama", "squad_load", "distinctive_spark") and delta < 0:
        return normalize_display_text(
            f"Voor {for_team} telt ook mee: {_after_colon_clause(reason)}"
        )

    if contrast and delta < 0 and for_team == loser:
        if fid in _LOSER_CONTRAST_PLAIN_IDS or reason.lower().startswith(loser.lower()):
            return normalize_display_text(reason)
        clause = _after_colon_clause(reason)
        if clause.lower().startswith(("uit tegen", "thuis in")):
            return ""
        return normalize_display_text(f"{loser} heeft last van: {clause}")

    if delta > 0:
        if reason.lower().startswith(for_team.lower()):
            return normalize_display_text(reason)
        return normalize_display_text(reason)

    return ""


def _lead_factor_sort_key(factor: dict[str, object]) -> tuple[int, int]:
    fid = str(factor["id"])
    generic = 2 if fid == "style_matchup" else (1 if fid in _DEPRIORITIZED_LEAD_IDS else 0)
    return (generic, -abs(int(factor["delta"])))


def _group_opponent_names_nl(fifa: str) -> list[str]:
    bundle = get_team_bundle(fifa)
    return [display_team_name(o) for o in bundle.group_stage.opponents_fifa]


def _primary_group_opponent(
    team: str, opponents: list[str], story_key: str
) -> str:
    ranked = sorted(
        opponents,
        key=lambda opp: hashlib.md5(f"{team}|{opp}|{story_key}".encode()).hexdigest(),
    )
    idx = int(hashlib.md5(f"{team}|{story_key}".encode()).hexdigest(), 16) % len(ranked)
    return ranked[idx]


def _is_primary_group_opponent(
    team: str, opponent: str, opponents: list[str], story_key: str
) -> bool:
    if not opponents:
        return False
    return opponent == _primary_group_opponent(team, opponents, story_key)


def _show_team_background_in_lead(
    team: str, opponent: str, group_opponents: list[str] | None
) -> bool:
    """Teamverhaal (James, Ancelotti) hooguit in één van de drie groepsduels."""
    if not group_opponents:
        return False
    return _is_primary_group_opponent(
        team, opponent, group_opponents, "persistent_story"
    )


def _include_persistent_cohost_story(
    team: str, opponent: str, group_opponents: list[str] | None
) -> bool:
    """Generieke co-hosttekst (meerdere wedstrijden in eigen regio) in max. 1 groepsduel."""
    if not group_opponents:
        return False
    return _is_primary_group_opponent(team, opponent, group_opponents, "cohost_story")


def _cohost_away_already_in_lead(factor: dict[str, object], sentences: list[str]) -> bool:
    """Geen dubbele co-host/venue-zin als de thuisploeg dat al noemt."""
    reason = str(factor.get("reason", "")).lower()
    venue_m = re.search(r"\(([^)]+)\)", reason)
    if venue_m:
        venue = venue_m.group(1).lower()
        return any(venue in s.lower() for s in sentences)
    return any("co-host" in s.lower() and "thuis" in s.lower() for s in sentences)


_OPENER_VENUE_OVERLAP_MARKERS = (
    "hoogte",
    "mexico city",
    "toronto",
    "co-host",
    "co host",
    "thuispubliek",
    "als co-host",
)


def _skip_opener_context_when_host_lead_already_covers_venue(
    factor: dict[str, object], sentences: list[str]
) -> bool:
    """Voorkom tweede zin die hoogte/co-host/publiek herhaalt na een host-openerregel."""
    if str(factor.get("id")) != "opener_context":
        return False
    reason = _clean_reason_text(str(factor.get("reason", "")))
    if not reason:
        return False
    low_r = reason.lower()
    openerish = (
        "openingswedstrijd" in low_r
        or "opent het wk" in low_r
        or " opent " in low_r
        or low_r.startswith("opent ")
    )
    if not openerish:
        return False
    blob = " ".join(sentences).lower()
    if len(blob) < 12:
        return False
    overlap = sum(
        1 for m in _OPENER_VENUE_OVERLAP_MARKERS if m in low_r and m in blob
    )
    return overlap >= 3


def _include_match_factor_in_lead(
    team: str,
    opponent: str,
    factor_id: str,
    *,
    group_opponents: list[str] | None = None,
) -> bool:
    """Generieke match-zinnen (zonder dekking, co-host opener) roteren per duel."""
    if factor_id in ("host_region", "cohost_crowd"):
        return _include_persistent_cohost_story(team, opponent, group_opponents)
    if factor_id not in ("matchup_edge", "fixture_story"):
        return True
    digest = hashlib.md5(f"{team}|{opponent}|{factor_id}".encode()).hexdigest()
    return int(digest, 16) % 3 == 0


def _build_why_from_factors(
    winner: str,
    loser: str,
    winner_factors: list[dict[str, object]],
    loser_factors: list[dict[str, object]],
    *,
    winner_group_opponents: list[str] | None = None,
) -> list[str]:
    win = _nonzero_factors(winner_factors)
    lose = _nonzero_factors(loser_factors)
    sentences: list[str] = []

    host_line = _narrate_host_bundle(
        winner, loser, win, group_opponents=winner_group_opponents
    )
    if host_line:
        sentences.append(host_line)

    style_in_lead = False
    for factor in sorted(
        (
            f
            for f in win
            if int(f["delta"]) > 0
            and str(f["id"]) not in _HOST_FACTOR_IDS
            and str(f.get("scope")) == "match"
        ),
        key=_lead_factor_sort_key,
    ):
        fid = str(factor["id"])
        if not _include_match_factor_in_lead(
            winner, loser, fid, group_opponents=winner_group_opponents
        ):
            continue
        if fid == "style_matchup":
            if style_in_lead:
                continue
            style_in_lead = True
        line = _sentence_from_factor(
            factor, winner=winner, loser=loser, for_team=winner
        )
        if line and line not in sentences:
            sentences.append(line)
        if len(sentences) >= 2:
            break

    for factor in sorted(
        (
            f
            for f in win
            if int(f["delta"]) < 0
            and str(f.get("scope")) == "match"
            and str(f["id"]) in _MATCH_NEGATIVE_IDS
        ),
        key=lambda f: abs(int(f["delta"])),
        reverse=True,
    ):
        if _skip_opener_context_when_host_lead_already_covers_venue(factor, sentences):
            continue
        line = _sentence_from_factor(
            factor, winner=winner, loser=loser, for_team=winner
        )
        if line and line not in sentences:
            sentences.append(line)
        if len(sentences) >= 2:
            break

    if len(sentences) < 2 and _show_team_background_in_lead(
        winner, loser, winner_group_opponents
    ):
        for factor in sorted(
            (f for f in win if int(f["delta"]) < 0 and str(f["id"]) in _TEAM_BACKGROUND_IDS),
            key=lambda f: abs(int(f["delta"])),
            reverse=True,
        ):
            line = _sentence_from_factor(
                factor, winner=winner, loser=loser, for_team=winner
            )
            if line and line not in sentences:
                sentences.append(line)
                break

    if len(sentences) < 3 and not any("telt ook mee" in s for s in sentences):
        for factor in sorted(
            (
                f
                for f in lose
                if int(f["delta"]) < 0 and str(f.get("scope")) == "match"
            ),
            key=lambda f: abs(int(f["delta"])),
            reverse=True,
        ):
            if str(factor["id"]) == "away_fixture" and _cohost_away_already_in_lead(
                factor, sentences
            ):
                continue
            if _skip_opener_context_when_host_lead_already_covers_venue(factor, sentences):
                continue
            line = _sentence_from_factor(
                factor,
                winner=winner,
                loser=loser,
                for_team=loser,
                contrast=True,
            )
            if line and line not in sentences:
                sentences.append(line)
                break

    if len(sentences) < 2:
        underdog_style_in_lead = style_in_lead
        for factor in sorted(
            (
                f
                for f in lose
                if int(f["delta"]) > 0
                and str(f.get("scope")) == "match"
                and str(f["id"]) not in _HOST_FACTOR_IDS
            ),
            key=_lead_factor_sort_key,
        ):
            fid = str(factor["id"])
            if fid == "style_matchup":
                if underdog_style_in_lead:
                    continue
                underdog_style_in_lead = True
            line = _sentence_from_factor(
                factor, winner=winner, loser=loser, for_team=loser
            )
            if line and line not in sentences and _is_usable_sentence(line):
                sentences.append(line)
            if len(sentences) >= 2:
                break

    if not sentences:
        for factor in sorted(
            (
                f
                for f in win
                if int(f["delta"]) > 0
                and str(f.get("scope")) == "match"
                and str(f["id"]) not in _HOST_FACTOR_IDS
            ),
            key=_lead_factor_sort_key,
        ):
            line = _sentence_from_factor(
                factor, winner=winner, loser=loser, for_team=winner
            )
            if line and _is_usable_sentence(line):
                sentences.append(line)
                break

    return sentences


def _is_usable_sentence(line: str) -> bool:
    text = line.strip().rstrip(".")
    if looks_truncated_reason(text):
        return False
    if len(text) < 24:
        return False
    words = text.split()
    if len(words) <= 2 and words[0][:1].isupper():
        return False
    low = text.lower()
    if _GENERIC_PROFITEERT_RE.search(text):
        return False
    if _VENUE_ONLY_RE.match(text.strip()):
        return False
    if "we profiteer" in low:
        return False
    if "leunt in dit duel op tegen " in low:
        return False
    if "leunt in dit duel op verde" in low:
        return False
    if "bondscoach van spanje" in low and "bielsa" in low:
        return False
    if "heeft last van:" in low and (
        "uit tegen co-host" in low or low.endswith("stadium).")
    ):
        return False
    return True


def _build_paper_strength_line(winner: str, loser: str, *, diff: int) -> str:
    """Kwalitatief voordeel zonder score-punten (zichtbaar vóór de uitklap)."""
    gap = abs(diff)
    if gap >= 12:
        return f"{winner} is op papier duidelijk sterker dan {loser}."
    if gap >= 6:
        return f"{winner} is op papier de favoriet tegen {loser}."
    if gap >= 3:
        return f"{winner} heeft op papier een licht voordeel op {loser}."
    return f"{winner} en {loser} liggen dicht bij elkaar; {winner} heeft op papier net iets meer."


def _build_draw_lead_summary(home_name: str, away_name: str) -> str:
    return (
        f"{home_name} en {away_name} liggen dicht bij elkaar; "
        f"het model voorspelt een gelijkspel."
    )


def _sentence_ok_for_draw_lead(sentence: str) -> bool:
    low = sentence.lower()
    blocked = (
        " wint",
        "wint.",
        "favoriet",
        "opent het wk",
        "openingsduel",
        "extra druk",
    )
    return not any(b in low for b in blocked)


def _build_lead_summary(
    pick: str,
    home_name: str,
    away_name: str,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
    *,
    diff: int,
    home_group_opponents: list[str] | None = None,
    away_group_opponents: list[str] | None = None,
) -> str:
    """Zichtbare samenvatting: research-context, geen wedstrijdscore-cijfers."""
    winner, loser = _winner_loser(pick, home_name, away_name)
    if not winner or not loser:
        if diff > 0:
            fav, under, fav_f, under_f = home_name, away_name, home_factors, away_factors
        elif diff < 0:
            fav, under, fav_f, under_f = away_name, home_name, away_factors, home_factors
        else:
            fav, under, fav_f, under_f = home_name, away_name, home_factors, away_factors
        fav_opps = (
            home_group_opponents
            if fav == home_name
            else away_group_opponents
        )
        sentences = [
            s
            for s in _build_why_from_factors(
                fav, under, fav_f, under_f, winner_group_opponents=fav_opps
            )
            if _is_usable_sentence(s) and _sentence_ok_for_draw_lead(s)
        ]
        opener = (
            f"{fav} heeft op papier een licht voordeel, maar het duel blijft open."
            if abs(diff) >= 3
            else f"{home_name} en {away_name} liggen dicht bij elkaar."
        )
        if sentences:
            return f"{opener} {sentences[0]}"
        return _build_draw_lead_summary(home_name, away_name)

    winner_factors = home_factors if winner == home_name else away_factors
    loser_factors = away_factors if loser == away_name else home_factors
    winner_opps = (
        home_group_opponents
        if winner == home_name
        else away_group_opponents
    )

    sentences: list[str] = []
    let_op_used = 0
    for s in _build_why_from_factors(
        winner,
        loser,
        winner_factors,
        loser_factors,
        winner_group_opponents=winner_opps,
    ):
        if not _is_usable_sentence(s):
            continue
        if s.lower().startswith("let op:"):
            let_op_used += 1
            if let_op_used > 1:
                continue
        if s in sentences:
            continue
        sentences.append(s)
    if sentences:
        return " ".join(sentences[:3])

    # Geen papieren-sterkte als lead: verdict + score-uitleg dekken dat al.
    return ""


def _lead_from_pool_adjustments(adjustments: list[dict[str, object]], *, limit: int = 2) -> str:
    """Korte lead uit poulevorm / pool-bijsturing (vooral knock-out)."""
    parts: list[str] = []
    for entry in adjustments:
        if not isinstance(entry, dict):
            continue
        reason = str(entry.get("reason", "")).strip()
        if reason:
            parts.append(reason)
        if len(parts) >= limit:
            break
    return " ".join(parts)


def _insight_payload(
    *,
    score_summary: str,
    lead_summary: str,
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
    home_research: int,
    home_host: int,
    home_travel: int,
    home_eff: int,
    away_research: int,
    away_host: int,
    away_travel: int,
    away_eff: int,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
    winner_side: str | None = None,
    base_diff: int | None = None,
    pool_adjustments: list[dict[str, object]] | None = None,
    pick_logic_note: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "scoreSummary": score_summary,
        "leadSummary": lead_summary,
        "verdict": verdict,
        "narrative": narrative,
        "steps": steps,
        "tags": tags,
        "diff": diff,
        "baseDiff": base_diff if base_diff is not None else diff,
        "poolAdjustments": pool_adjustments or [],
        "pickLogicNote": pick_logic_note,
        "home": {
            "team": home_name,
            "powerScore": home_power,
            "contextDelta": home_ctx,
            "researchDelta": home_research,
            "hostDelta": home_host,
            "travelDelta": home_travel,
            "effectiveScore": home_eff,
            "factors": home_factors,
        },
        "away": {
            "team": away_name,
            "powerScore": away_power,
            "contextDelta": away_ctx,
            "researchDelta": away_research,
            "hostDelta": away_host,
            "travelDelta": away_travel,
            "effectiveScore": away_eff,
            "factors": away_factors,
        },
    }
    if winner_side:
        payload["winnerSide"] = winner_side
    return payload
