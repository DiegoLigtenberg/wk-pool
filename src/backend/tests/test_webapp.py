from app.tournament import build_tournament_view, load_fixtures
from app.webapp import health_payload


def test_health_payload_identifies_backend() -> None:
    assert health_payload() == {"status": "ok", "service": "wk-pool-backend"}


def test_load_fixtures_reads_world_cup_csv() -> None:
    fixtures = load_fixtures()

    assert len(fixtures) == 104
    assert fixtures[0].home_team == "Mexico"
    assert fixtures[0].away_team == "South Africa"
    assert fixtures[0].group == "A"


def test_tournament_view_contains_pickem_preview() -> None:
    tournament = build_tournament_view()
    summary = tournament["summary"]

    assert summary["groupMatches"] == 72
    assert summary["completed"] == 36
    assert summary["aiCorrect"] + summary["aiWrong"] == 36
    assert len(tournament["groups"]) == 12
