import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "fifa-world-cup-2026-UTC.csv"
FINISHED_MATCH_COUNT = 36
PICKS = ("1", "2", "3")
FAKE_SCORES = (
    (2, 0),
    (1, 1),
    (0, 1),
    (3, 1),
    (1, 0),
    (2, 2),
    (0, 0),
    (1, 2),
)


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
    matches = [_match_view(fixture) for fixture in fixtures]
    group_stage_matches = [match for match in matches if match["stage"] == "group"]
    completed_matches = [match for match in matches if match["status"] == "completed"]
    upcoming_matches = [match for match in matches if match["status"] == "upcoming"]
    prediction_summary = _prediction_summary(group_stage_matches)

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
        "nextMatch": upcoming_matches[0] if upcoming_matches else None,
        "recentMatches": completed_matches[-6:],
        "upcomingMatches": upcoming_matches[:8],
        "groups": _group_views(group_stage_matches),
        "knockoutMatches": [match for match in matches if match["stage"] == "knockout"],
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


def _match_view(fixture: Fixture) -> dict[str, object]:
    is_group_match = fixture.group is not None
    is_completed = is_group_match and fixture.match_number <= FINISHED_MATCH_COUNT
    score = _fake_score(fixture) if is_completed else None
    actual_pick = _actual_pick(score) if score else None
    ai_pick = _ai_pick(fixture)
    prediction_status = _prediction_status(ai_pick, actual_pick)

    return {
        "matchNumber": fixture.match_number,
        "round": fixture.round_number,
        "stage": "group" if is_group_match else "knockout",
        "group": fixture.group,
        "kickoffAt": fixture.kickoff_at.isoformat().replace("+00:00", "Z"),
        "location": fixture.location,
        "homeTeam": fixture.home_team,
        "awayTeam": fixture.away_team,
        "status": "completed" if is_completed else "upcoming",
        "score": _score_view(score),
        "actualPick": actual_pick,
        "aiPrediction": {
            "pick": ai_pick,
            "confidence": _confidence(fixture),
            "explanation": _explanation(fixture, ai_pick),
            "status": prediction_status,
        },
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
            }
        )

    return groups


def _standings(matches: list[dict[str, object]]) -> list[dict[str, object]]:
    table: dict[str, dict[str, object]] = {}

    for match in matches:
        _ensure_team(table, str(match["homeTeam"]))
        _ensure_team(table, str(match["awayTeam"]))

        if match["status"] != "completed" or not match["score"]:
            continue

        score = match["score"]
        home_team = str(match["homeTeam"])
        away_team = str(match["awayTeam"])
        home_goals = int(score["home"])
        away_goals = int(score["away"])
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


def _fake_score(fixture: Fixture) -> tuple[int, int]:
    return FAKE_SCORES[(fixture.match_number - 1) % len(FAKE_SCORES)]


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


def _ai_pick(fixture: Fixture) -> str:
    return PICKS[(fixture.match_number + len(fixture.home_team)) % len(PICKS)]


def _confidence(fixture: Fixture) -> int:
    return 54 + ((fixture.match_number * 7) % 37)


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


def _explanation(fixture: Fixture, ai_pick: str) -> str:
    if ai_pick == "1":
        choice = "het thuisland"
        reason = "meer verwachte controle en een licht voordeel in deze wedstrijd"
    elif ai_pick == "2":
        choice = "het uitland"
        reason = "meer dreiging in de omschakeling en een hogere kans op een verrassing"
    else:
        choice = "een gelijkspel"
        reason = "weinig verschil tussen beide landen in de voorspelling"

    return f"De AI kiest voor {choice}, door {reason}."
