"""Tests for knockout round form blending."""

from app.knockout_form import blended_goals_per_game


def test_blended_goals_per_game_uses_knockout_when_available() -> None:
    blended = blended_goals_per_game(2.0, 1.0, knockout_played=1)
    assert 1.0 < blended < 2.0
    assert blended == 0.55 * 2.0 + 0.45 * 1.0


def test_blended_goals_per_game_falls_back_to_group() -> None:
    assert blended_goals_per_game(2.0, 1.0, knockout_played=0) == 2.0
