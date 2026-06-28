import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.match_results_store import load_results, result_for_match
from app.knockout_bracket import build_knockout_bracket_state, resolve_knockout_teams
from app.group_form import build_group_form_index
from app.predictions import is_known_team, predict_match, team_insight
from app.teams import display_team_name


CSV_PATH = Path(__file__).resolve().parent / "data" / "fifa-world-cup-2026-UTC.csv"


@dataclass(frozen=True)
class Fixture:
    match_number: int
    round_number: str
    kickoff_at: datetime
    location: str
    home_team: str
    away_team: str
    group: str | None


def load_fixtures(path: Path = CSV_PATH) -> list[Fixture]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        rows = csv.DictReader(file)
        fixtures = [_fixture_from_row(row) for row in rows]

    return sorted(fixtures, key=lambda fixture: fixture.match_number)


def build_tournament_view(path: Path = CSV_PATH) -> dict[str, object]:
    fixtures = load_fixtures(path)
    results_store = load_results()
    bracket = build_knockout_bracket_state(fixtures, results_store)
    form_index = build_group_form_index(fixtures, results_store) if bracket else {}
    matches = [
        _match_view(fixture, results_store, bracket=bracket, form_index=form_index)
        for fixture in fixtures
    ]
    group_stage_matches = [match for match in matches if match["stage"] == "group"]
    completed_matches = [match for match in matches if match["status"] == "completed"]
    upcoming_matches = [match for match in matches if match["status"] == "upcoming"]
    completed_by_kickoff = sorted(completed_matches, key=_match_kickoff)
    upcoming_by_kickoff = sorted(upcoming_matches, key=_match_kickoff)
    prediction_summary = _prediction_summary(group_stage_matches)
    groups = _group_views(group_stage_matches)
    from app.crystal_ball import build_crystal_ball_view

    return {
        "summary": {
            "totalMatches": len(matches),
            "groupMatches": len(group_stage_matches),
            "completed": len(completed_matches),
            "upcoming": len(upcoming_matches),
            "aiCorrect": prediction_summary["correct"],
            "aiWrong": prediction_summary["wrong"],
            "aiPending": prediction_summary["pending"],
            "aiAccuracy": prediction_summary["accuracy"],
        },
        "nextMatch": upcoming_by_kickoff[0] if upcoming_by_kickoff else None,
        "recentMatches": completed_by_kickoff[-6:],
        "upcomingMatches": upcoming_by_kickoff[:8],
        "teamInsights": _team_insights(fixtures, bracket=bracket),
        "groups": groups,
        "knockoutMatches": [match for match in matches if match["stage"] == "knockout"],
        "crystalBall": build_crystal_ball_view(
            group_stage_matches,
            results_store=results_store,
            completed_count=len(completed_matches),
            total_count=len(matches),
            group_winner_status={
                str(group["name"]): str(group["winnerPredictionStatus"]) for group in groups
            },
        ),
        "cardTotals": results_store.get("tournamentTotals", {"yellowCards": 0, "directRedCards": 0}),
        "resultsUpdatedAt": results_store.get("updatedAt"),
    }


def _fixture_from_row(row: dict[str, str]) -> Fixture:
    kickoff_at = datetime.strptime(row["Date"], "%d/%m/%Y %H:%M").replace(
        tzinfo=timezone.utc
    )
    group = row["Group"].removeprefix("Group ").strip() or None
    return Fixture(
        match_number=int(row["Match Number"]),
        round_number=row["Round Number"],
        kickoff_at=kickoff_at,
        location=row["Location"],
        home_team=row["Home Team"],
        away_team=row["Away Team"],
        group=group,
    )


def _match_kickoff(match: dict[str, object]) -> str:
    return str(match["kickoffAt"])


def _match_view(
    fixture: Fixture,
    results_store: dict[str, object] | None = None,
    *,
    bracket=None,
    form_index: dict | None = None,
) -> dict[str, object]:
    is_group_match = fixture.group is not None
    stored = result_for_match(results_store or {}, fixture.match_number) if results_store else None
    score_tuple: tuple[int, int] | None = None
    if stored and isinstance(stored.get("score"), dict):
        score_tuple = (int(stored["score"]["home"]), int(stored["score"]["away"]))

    home_team = fixture.home_team
    away_team = fixture.away_team
    group_forms = None
    if not is_group_match and bracket is not None:
        home_team, away_team = resolve_knockout_teams(fixture, bracket)
        if form_index:
            group_forms = (form_index.get(home_team), form_index.get(away_team))

    ai_prediction = predict_match(
        home_team,
        away_team,
        "group" if is_group_match else "knockout",
        fixture.round_number,
        fixture.group,
        match_number=fixture.match_number,
        group_forms=group_forms,
    )
    ai_pick = str(ai_prediction["pick"])
    actual_pick = _actual_pick(score_tuple) if score_tuple else None
    prediction_status = _prediction_status(ai_pick, actual_pick)
    is_completed = score_tuple is not None

    return {
        "matchNumber": fixture.match_number,
        "round": fixture.round_number,
        "stage": "group" if is_group_match else "knockout",
        "group": fixture.group,
        "kickoffAt": fixture.kickoff_at.isoformat().replace("+00:00", "Z"),
        "location": fixture.location,
        "homeTeam": display_team_name(home_team),
        "awayTeam": display_team_name(away_team),
        "status": "completed" if is_completed else "upcoming",
        "score": _score_view(score_tuple),
        "actualPick": actual_pick,
        "aiPrediction": _ai_prediction_view(ai_prediction, prediction_status),
    }


def _ai_prediction_view(prediction: dict[str, object], status: str) -> dict[str, object]:
    """API view; includes legacy ``themes`` for older frontends still deployed."""
    view: dict[str, object] = {**prediction, "status": status}
    if "themes" not in view:
        insight = view.get("insight")
        if isinstance(insight, dict) and isinstance(insight.get("tags"), list):
            view["themes"] = [str(tag) for tag in insight["tags"]]
        else:
            view["themes"] = []
    return view


def _team_insights(fixtures: list[Fixture], *, bracket=None) -> dict[str, object]:
    teams: set[str] = set()
    for fixture in fixtures:
        for team in (fixture.home_team, fixture.away_team):
            if is_known_team(team):
                teams.add(team)
    if bracket is not None:
        for home, away in bracket.resolved_teams.values():
            for team in (home, away):
                if team and is_known_team(team):
                    teams.add(team)
    return {
        display_team_name(team): insight
        for team in sorted(teams)
        if (insight := team_insight(team))
    }


def _group_views(matches: list[dict[str, object]]) -> list[dict[str, object]]:
    group_names = sorted({match["group"] for match in matches if match["group"]})
    groups = []

    for group_name in group_names:
        group_matches = [match for match in matches if match["group"] == group_name]
        groups.append(
            {
                "name": group_name,
                "standings": _standings(group_matches),
                "matches": group_matches,
                **_group_winner_prediction_fields(group_matches),
            }
        )

    return groups


def _group_winner_prediction_fields(
    group_matches: list[dict[str, object]],
) -> dict[str, str]:
    projected = _standings(group_matches, from_picks=True)
    predicted = str(projected[0]["team"]) if projected else ""
    completed = sum(1 for match in group_matches if match["status"] == "completed")

    if completed == 0 or not predicted:
        status = "pending"
    else:
        leader = str(_standings(group_matches)[0]["team"])
        status = "correct" if leader == predicted else "wrong"

    return {
        "predictedWinner": predicted,
        "winnerPredictionStatus": status,
    }


def _score_from_pick(pick: str) -> tuple[int, int]:
    if pick == "1":
        return (1, 0)
    if pick == "2":
        return (0, 1)
    return (1, 1)


def _standings(
    matches: list[dict[str, object]],
    *,
    from_picks: bool = False,
) -> list[dict[str, object]]:
    table: dict[str, dict[str, object]] = {}

    for match in matches:
        _ensure_team(table, str(match["homeTeam"]))
        _ensure_team(table, str(match["awayTeam"]))

        if from_picks:
            prediction = match.get("aiPrediction")
            if not isinstance(prediction, dict):
                continue
            home_goals, away_goals = _score_from_pick(str(prediction["pick"]))
        elif match["status"] != "completed" or not match["score"]:
            continue
        else:
            score = match["score"]
            home_goals = int(score["home"])
            away_goals = int(score["away"])

        home_team = str(match["homeTeam"])
        away_team = str(match["awayTeam"])
        _apply_result(table[home_team], home_goals, away_goals)
        _apply_result(table[away_team], away_goals, home_goals)

    return sorted(
        table.values(),
        key=lambda team: (-int(team["points"]), -int(team["goalDifference"]), str(team["team"])),
    )


def _ensure_team(table: dict[str, dict[str, object]], team: str) -> None:
    table.setdefault(
        team,
        {
            "team": team,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goalsFor": 0,
            "goalsAgainst": 0,
            "goalDifference": 0,
            "points": 0,
        },
    )


def _apply_result(team: dict[str, object], goals_for: int, goals_against: int) -> None:
    team["played"] = int(team["played"]) + 1
    team["goalsFor"] = int(team["goalsFor"]) + goals_for
    team["goalsAgainst"] = int(team["goalsAgainst"]) + goals_against
    team["goalDifference"] = int(team["goalsFor"]) - int(team["goalsAgainst"])

    if goals_for > goals_against:
        team["wins"] = int(team["wins"]) + 1
        team["points"] = int(team["points"]) + 3
    elif goals_for == goals_against:
        team["draws"] = int(team["draws"]) + 1
        team["points"] = int(team["points"]) + 1
    else:
        team["losses"] = int(team["losses"]) + 1


def _score_view(score: tuple[int, int] | None) -> dict[str, int] | None:
    if score is None:
        return None

    return {"home": score[0], "away": score[1]}


def _actual_pick(score: tuple[int, int]) -> str:
    if score[0] > score[1]:
        return "1"
    if score[1] > score[0]:
        return "2"
    return "3"


def _prediction_status(ai_pick: str, actual_pick: str | None) -> str:
    if actual_pick is None:
        return "pending"
    if ai_pick == actual_pick:
        return "correct"
    return "wrong"


def _prediction_summary(matches: list[dict[str, object]]) -> dict[str, int | float]:
    correct = 0
    wrong = 0
    pending = 0

    for match in matches:
        prediction = match["aiPrediction"]
        status = str(prediction["status"])
        if status == "correct":
            correct += 1
        elif status == "wrong":
            wrong += 1
        else:
            pending += 1

    decided = correct + wrong
    accuracy = round((correct / decided) * 100, 1) if decided else 0
    return {"correct": correct, "wrong": wrong, "pending": pending, "accuracy": accuracy}

