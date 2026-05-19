"""Tournament context schema in team-YAML."""

from pathlib import Path

import yaml

from app.data.teams.team_loader import get_team_bundle
from app.data.teams.tournament_context_loader import head_to_head_vs, parse_tournament_context


def test_parse_tournament_context_from_snippet() -> None:
    raw = yaml.safe_load(
        """
tournament_context:
  schema_version: 1
  phases:
    group:
      status: in_progress
      fixture_plan:
        group: F
        opponents_nl: [Japan]
        opponents_fifa: [Japan]
        fixtures:
          - match_number: 1
            kickoff: "2026-06-14T20:00"
            is_home: true
            opponent_fifa: Japan
            opponent_nl: Japan
            stadium: Dallas Stadium
        fixture_hooks: []
        schedule_rest_notes: null
        venue_dispersion_notes: "test"
      played_matches:
        - match_number: 1
          opponent_fifa: Japan
          opponent_nl: Japan
          result: W
          score_for: 2
          score_against: 1
      standings:
        points: 3
        played: 1
        wins: 1
        draws: 0
        losses: 0
        goals_for: 2
        goals_against: 1
        position: 1
      momentum:
        label: rising
        notes: "Goede start"
    knockout:
      status: not_applicable
  head_to_head:
    - opponent_fifa: Brazil
      opponent_nl: Brazilië
      scope: world_cup
      wins: 0
      draws: 1
      losses: 1
"""
    )
    tc = parse_tournament_context(raw["tournament_context"])
    assert tc is not None
    assert tc.phases["group"].status == "in_progress"
    assert len(tc.phases["group"].played_matches) == 1
    assert tc.phases["group"].played_matches[0].result == "W"
    assert tc.phases["group"].momentum is not None
    assert tc.phases["group"].momentum.label == "rising"
    h2h = head_to_head_vs(tc, "Brazil", scope="world_cup")
    assert h2h is not None
    assert h2h.losses == 1


def test_netherlands_bundle_has_group_stage() -> None:
    bundle = get_team_bundle("Netherlands")
    assert bundle.group_stage.group == "F"
    assert len(bundle.group_stage.fixtures) == 3
