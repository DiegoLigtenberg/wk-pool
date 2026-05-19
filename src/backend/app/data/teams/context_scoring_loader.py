"""YAML `context_scoring` → ContextScoring."""

from __future__ import annotations

from typing import Any

from app.data.teams.context_scoring_schema import ContextFactor, ContextScoring
from app.teams import fifa_team_key


def _parse_factors(raw: object, *, label: str) -> tuple[ContextFactor, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise TypeError(f"{label} must be a list")
    out: list[ContextFactor] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TypeError(f"{label} items must be objects")
        out.append(
            ContextFactor(
                id=str(item["id"]),
                delta=int(item["delta"]),
                reason=str(item["reason"]),
            )
        )
    return tuple(out)


def parse_context_scoring(raw: object) -> ContextScoring | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeError("context_scoring must be a mapping")
    persistent = _parse_factors(raw.get("persistent"), label="context_scoring.persistent")
    versus_raw = raw.get("versus") or {}
    if not isinstance(versus_raw, dict):
        raise TypeError("context_scoring.versus must be a mapping")
    versus: dict[str, tuple[ContextFactor, ...]] = {}
    for opp, factors in versus_raw.items():
        versus[fifa_team_key(str(opp))] = _parse_factors(factors, label=f"context_scoring.versus[{opp}]")
    return ContextScoring(persistent=persistent, versus=versus)
