"""Gestructureerde research-context → kleine score-delta's per wedstrijd."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextFactor:
    """Eén uitlegbare correctie (punten-equivalent op diff)."""

    id: str
    delta: int
    reason: str


@dataclass(frozen=True, slots=True)
class ContextScoring:
    """Vooraf vastgelegde context (1× per land, groepsfase bekend)."""

    persistent: tuple[ContextFactor, ...]  # elk groepsduel
    versus: dict[str, tuple[ContextFactor, ...]]  # opponent_fifa → factoren
