"""Tests for knockout round form blending."""

from app.knockout_form import blended_goals_per_game


def test_blended_goals_per_game_uses_knockout_when_available() -> None:
    blended = blended_goals_per_game(2.0, 1.0, knockout_played=1)
    assert 1.0 < blended < 2.0
    assert blended == 0.55 * 2.0 + 0.45 * 1.0


def test_blended_goals_per_game_falls_back_to_group() -> None:
    assert blended_goals_per_game(2.0, 1.0, knockout_played=0) == 2.0


def test_knockout_form_includes_r16_for_quarter_finals() -> None:
    from app.knockout_bracket import build_knockout_bracket_state
    from app.knockout_form import _round_rank, build_knockout_round_form_index
    from app.match_results_store import load_results
    from app.tournament import load_fixtures

    assert _round_rank("Round of 32") > _round_rank("Round of 16") > _round_rank("Quarter Finals")
    fixtures = load_fixtures()
    store = load_results()
    bracket = build_knockout_bracket_state(fixtures, store)
    assert bracket is not None
    qf_form = build_knockout_round_form_index(
        fixtures,
        store,
        bracket.resolved_teams,
        before_round="Quarter Finals",
    )
    assert "France" in qf_form
    assert qf_form["France"].played >= 2
