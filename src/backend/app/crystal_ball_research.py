"""Laad Crystal Ball bonus-onderzoek uit YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

RESEARCH_DIR = Path(__file__).resolve().parent / "data" / "crystal-ball-research"
DEFAULT_FILE = RESEARCH_DIR / "tournament_2026.yaml"

BONUS_LABELS: dict[str, str] = {
    "yellow_cards_total": "Gele kaarten",
    "direct_red_cards": "Direct rood",
    "champion": "Wereldkampioen",
    "top_scorer": "Topscorer",
}


@lru_cache(maxsize=1)
def load_crystal_ball_research(path: Path = DEFAULT_FILE) -> dict[str, object]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping at root")

    raw_questions = data.get("bonus_questions")
    if not isinstance(raw_questions, dict):
        raise ValueError(f"{path}: bonus_questions missing or not a mapping")

    bonus_questions: list[dict[str, str]] = []
    for question_id, label in BONUS_LABELS.items():
        entry = raw_questions.get(question_id)
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: bonus_questions.{question_id} missing")
        bonus_questions.append(_bonus_view(question_id, label, entry))

    return {
        "id": str(data.get("id", path.stem)),
        "contextAsOf": str(data.get("context_as_of", "")),
        "sources": [str(source) for source in data.get("sources") or []],
        "bonusQuestions": bonus_questions,
    }


def _bonus_view(question_id: str, label: str, entry: dict[str, Any]) -> dict[str, str]:
    value = entry.get("value")
    helper = entry.get("helper")
    rationale = entry.get("rationale")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"bonus_questions.{question_id}.value must be a non-empty string")
    if not isinstance(helper, str) or not helper.strip():
        raise ValueError(f"bonus_questions.{question_id}.helper must be a non-empty string")

    view: dict[str, str] = {
        "id": question_id,
        "label": label,
        "value": value.strip(),
        "helper": helper.strip(),
    }
    if isinstance(rationale, str) and rationale.strip():
        view["rationale"] = rationale.strip()
    return view
