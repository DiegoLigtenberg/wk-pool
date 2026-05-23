"""Per-duel upset/choke-notities uit team-YAML (niet land-breed)."""

from __future__ import annotations

from typing import Any

from app.teams import fifa_team_key


def parse_matchup_volatility(raw: object) -> dict[str, dict[str, str]]:
    """`matchup_volatility` → {opponent_fifa: {upset?: str, choke?: str}}."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError("matchup_volatility must be a mapping")

    out: dict[str, dict[str, str]] = {}
    for opp, entry in raw.items():
        opp_key = fifa_team_key(str(opp))
        if isinstance(entry, str):
            text = entry.strip()
            if text:
                out[opp_key] = {"upset": text}
            continue
        if not isinstance(entry, dict):
            raise TypeError(f"matchup_volatility[{opp!r}] must be str or mapping")
        parsed: dict[str, str] = {}
        for kind in ("upset", "choke"):
            value = entry.get(kind)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                parsed[kind] = text
        if parsed:
            out[opp_key] = parsed
    return out
